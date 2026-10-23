using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Interfaces.Repositories;
using ErsatzTV.Core.Streaming;
using Microsoft.Extensions.Logging;
using NSubstitute;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Streaming;

[TestFixture]
public class ChannelFallbackSlateServiceTests
{
    private IMediaCollectionRepository _mediaCollectionRepository;
    private ILogger<ChannelFallbackSlateService> _logger;
    private ChannelFallbackSlateService _service;

    [SetUp]
    public void SetUp()
    {
        _mediaCollectionRepository = Substitute.For<IMediaCollectionRepository>();
        _logger = Substitute.For<ILogger<ChannelFallbackSlateService>>();
        _service = new ChannelFallbackSlateService(_mediaCollectionRepository, _logger);
    }

    [Test]
    public async Task GetFallbackMediaItem_Should_Return_None_When_Slate_Disabled()
    {
        var channel = new Channel(Guid.NewGuid())
        {
            FallbackSlate = new ChannelFallbackSlate { Mode = FallbackSlateMode.Disabled }
        };

        var result = await _service.GetFallbackMediaItem(channel, CancellationToken.None);
        result.IsNone.ShouldBeTrue();
    }

    [Test]
    public async Task GetFallbackMediaItem_Should_Resolve_SingleMedia()
    {
        var slate = new ChannelFallbackSlate
        {
            Mode = FallbackSlateMode.SingleMedia,
            MediaItemId = 99
        };

        var channel = new Channel(Guid.NewGuid()) { FallbackSlate = slate };
        var movie = new Movie { Id = 99 };
        _mediaCollectionRepository.GetMovie(99).Returns(new List<Movie> { movie });

        var result = await _service.GetFallbackMediaItem(channel, CancellationToken.None);
        result.IsSome.ShouldBeTrue();
        foreach (MediaItem item in result)
        {
            item.Id.ShouldBe(99);
        }
    }

    [Test]
    public async Task GetFallbackMediaItem_Should_Resolve_Collection()
    {
        var slate = new ChannelFallbackSlate
        {
            Mode = FallbackSlateMode.Collection,
            CollectionId = 15
        };

        var channel = new Channel(Guid.NewGuid()) { FallbackSlate = slate };
        var movie = new Movie { Id = 150 };
        _mediaCollectionRepository.GetItems(15).Returns(new List<MediaItem> { movie });

        var result = await _service.GetFallbackMediaItem(channel, CancellationToken.None);
        result.IsSome.ShouldBeTrue();
        foreach (MediaItem item in result)
        {
            item.Id.ShouldBe(150);
        }
    }

    [Test]
    public async Task CreateFallbackPlayoutItem_Should_Create_Item_With_Fallback_Kind()
    {
        var slate = new ChannelFallbackSlate
        {
            Mode = FallbackSlateMode.SingleMedia,
            MediaItemId = 88,
            CustomTitle = "Sinal Técnico HMCast"
        };

        var channel = new Channel(Guid.NewGuid()) { FallbackSlate = slate };
        var movie = new Movie { Id = 88 };
        _mediaCollectionRepository.GetMovie(88).Returns(new List<Movie> { movie });

        var start = DateTimeOffset.UtcNow;
        var duration = TimeSpan.FromMinutes(15);

        var result = await _service.CreateFallbackPlayoutItem(channel, start, duration, CancellationToken.None);
        result.IsSome.ShouldBeTrue();

        foreach (PlayoutItem playoutItem in result)
        {
            playoutItem.MediaItemId.ShouldBe(88);
            playoutItem.Start.ShouldBe(start.UtcDateTime);
            playoutItem.Finish.ShouldBe(start.Add(duration).UtcDateTime);
            playoutItem.FillerKind.ShouldBe(FillerKind.Fallback);
            playoutItem.CustomTitle.ShouldBe("Sinal Técnico HMCast");
        }
    }
}
