using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Interfaces.Repositories;
using ErsatzTV.Core.Streaming;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using NSubstitute;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Streaming;

[TestFixture]
public class ChannelPreCacheServiceTests
{
    private IServiceScopeFactory _scopeFactory;
    private IServiceScope _scope;
    private IServiceProvider _serviceProvider;
    private IChannelRepository _channelRepository;
    private ILogger<ChannelPreCacheService> _logger;
    private ChannelPreCacheService _service;

    [SetUp]
    public void SetUp()
    {
        _scopeFactory = Substitute.For<IServiceScopeFactory>();
        _scope = Substitute.For<IServiceScope>();
        _serviceProvider = Substitute.For<IServiceProvider>();
        _channelRepository = Substitute.For<IChannelRepository>();
        _logger = Substitute.For<ILogger<ChannelPreCacheService>>();

        _scopeFactory.CreateScope().Returns(_scope);
        _scope.ServiceProvider.Returns(_serviceProvider);
        _serviceProvider.GetService(typeof(IChannelRepository)).Returns(_channelRepository);

        _service = new ChannelPreCacheService(_scopeFactory, _logger);
    }

    [Test]
    public async Task WarmupChannel_Should_Store_Session_When_PreCache_Enabled()
    {
        var channel = new Channel(Guid.NewGuid())
        {
            Id = 1,
            Number = "1.1",
            IdleBehavior = ChannelIdleBehavior.PreCache,
            IsEnabled = true
        };

        var movie = new Movie
        {
            Id = 10,
            MediaVersions = new List<MediaVersion>
            {
                new()
                {
                    MediaFiles = new List<MediaFile>
                    {
                        new() { Path = "/media/movies/inception.mp4" }
                    }
                }
            }
        };

        var now = DateTimeOffset.UtcNow;
        var currentItem = new PlayoutItem
        {
            MediaItem = movie,
            Start = now.AddMinutes(-10).UtcDateTime,
            Finish = now.AddMinutes(20).UtcDateTime
        };

        var nextItem = new PlayoutItem
        {
            Start = now.AddMinutes(20).UtcDateTime,
            Finish = now.AddMinutes(50).UtcDateTime
        };

        var playout = new Playout
        {
            IsEnabled = true,
            Items = new List<PlayoutItem> { currentItem, nextItem }
        };

        channel.Playouts = new List<Playout> { playout };
        _channelRepository.GetByNumber("1.1").Returns(channel);

        await _service.WarmupChannel("1.1", CancellationToken.None);

        var maybeSession = _service.GetPreCachedSession("1.1");
        maybeSession.IsSome.ShouldBeTrue();

        foreach (PreCachedChannelSession session in maybeSession)
        {
            session.ChannelNumber.ShouldBe("1.1");
            session.ChannelId.ShouldBe(1);
            session.MediaFilePath.ShouldBe("/media/movies/inception.mp4");
            session.CurrentSeek.TotalMinutes.ShouldBeGreaterThan(9);
            session.CurrentItem.ShouldBe(currentItem);
            session.NextItem.ShouldBe(nextItem);
        }
    }

    [Test]
    public async Task WarmupChannel_Should_Ignore_When_IdleBehavior_Is_Not_PreCache()
    {
        var channel = new Channel(Guid.NewGuid())
        {
            Id = 2,
            Number = "2.1",
            IdleBehavior = ChannelIdleBehavior.StopOnDisconnect,
            IsEnabled = true
        };

        _channelRepository.GetByNumber("2.1").Returns(channel);

        await _service.WarmupChannel("2.1", CancellationToken.None);

        var maybeSession = _service.GetPreCachedSession("2.1");
        maybeSession.IsNone.ShouldBeTrue();
    }

    [Test]
    public async Task GetPreCachedSession_Should_Evict_Expired_Session()
    {
        var channel = new Channel(Guid.NewGuid())
        {
            Id = 3,
            Number = "3.1",
            IdleBehavior = ChannelIdleBehavior.PreCache,
            IsEnabled = true
        };

        var now = DateTimeOffset.UtcNow;
        var expiredItem = new PlayoutItem
        {
            Start = now.AddMinutes(-30).UtcDateTime,
            Finish = now.AddMilliseconds(-100).UtcDateTime // já expirado
        };

        var playout = new Playout
        {
            IsEnabled = true,
            Items = new List<PlayoutItem> { expiredItem }
        };

        channel.Playouts = new List<Playout> { playout };
        _channelRepository.GetByNumber("3.1").Returns(channel);

        await _service.WarmupChannel("3.1", CancellationToken.None);

        // Ao buscar, o serviço deve identificar que expirou e remover da RAM
        var maybeSession = _service.GetPreCachedSession("3.1");
        maybeSession.IsNone.ShouldBeTrue();
    }

    [Test]
    public async Task Invalidate_Should_Remove_Cached_Session()
    {
        var channel = new Channel(Guid.NewGuid())
        {
            Id = 4,
            Number = "4.1",
            IdleBehavior = ChannelIdleBehavior.PreCache,
            IsEnabled = true
        };

        var now = DateTimeOffset.UtcNow;
        var item = new PlayoutItem
        {
            Start = now.AddMinutes(-5).UtcDateTime,
            Finish = now.AddMinutes(25).UtcDateTime
        };

        var playout = new Playout
        {
            IsEnabled = true,
            Items = new List<PlayoutItem> { item }
        };

        channel.Playouts = new List<Playout> { playout };
        _channelRepository.GetByNumber("4.1").Returns(channel);

        await _service.WarmupChannel("4.1", CancellationToken.None);
        _service.GetPreCachedSession("4.1").IsSome.ShouldBeTrue();

        _service.Invalidate("4.1");
        _service.GetPreCachedSession("4.1").IsNone.ShouldBeTrue();
    }

    [Test]
    public async Task UpdateSeek_Should_Update_Session_Seek()
    {
        var channel = new Channel(Guid.NewGuid())
        {
            Id = 5,
            Number = "5.1",
            IdleBehavior = ChannelIdleBehavior.PreCache,
            IsEnabled = true
        };

        var now = DateTimeOffset.UtcNow;
        var item = new PlayoutItem
        {
            Start = now.AddMinutes(-5).UtcDateTime,
            Finish = now.AddMinutes(25).UtcDateTime
        };

        var playout = new Playout
        {
            IsEnabled = true,
            Items = new List<PlayoutItem> { item }
        };

        channel.Playouts = new List<Playout> { playout };
        _channelRepository.GetByNumber("5.1").Returns(channel);

        await _service.WarmupChannel("5.1", CancellationToken.None);

        var newSeek = TimeSpan.FromMinutes(12);
        _service.UpdateSeek("5.1", newSeek);

        var session = (PreCachedChannelSession)_service.GetPreCachedSession("5.1");
        session.CurrentSeek.ShouldBe(newSeek);
    }

    [Test]
    public async Task Performance_ZeroDelay_Access_Should_Return_In_Sub_Millisecond()
    {
        // TASK-4.2: Validação de performance e prontidão imediata do buffer
        var channel = new Channel(Guid.NewGuid())
        {
            Id = 6,
            Number = "6.1",
            IdleBehavior = ChannelIdleBehavior.PreCache,
            IsEnabled = true
        };

        var now = DateTimeOffset.UtcNow;
        var item = new PlayoutItem
        {
            Start = now.AddMinutes(-1).UtcDateTime,
            Finish = now.AddHours(1).UtcDateTime
        };

        var playout = new Playout
        {
            IsEnabled = true,
            Items = new List<PlayoutItem> { item }
        };

        channel.Playouts = new List<Playout> { playout };
        _channelRepository.GetByNumber("6.1").Returns(channel);

        await _service.WarmupChannel("6.1", CancellationToken.None);

        // Aferir latência de 10.000 lookups em RAM
        var stopwatch = Stopwatch.StartNew();
        const int iterations = 10_000;
        for (int i = 0; i < iterations; i++)
        {
            var res = _service.GetPreCachedSession("6.1");
            res.IsSome.ShouldBeTrue();
        }
        stopwatch.Stop();

        double averageMicroseconds = (stopwatch.Elapsed.TotalMilliseconds * 1000.0) / iterations;
        // Lookup em RAM deve ser instantâneo (< 100 microssegundos por operação)
        averageMicroseconds.ShouldBeLessThan(100.0);
    }
}
