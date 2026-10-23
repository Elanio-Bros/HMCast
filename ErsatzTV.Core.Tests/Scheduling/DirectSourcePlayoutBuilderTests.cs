using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Interfaces.Repositories;
using ErsatzTV.Core.Scheduling;
using Microsoft.Extensions.Logging;
using NSubstitute;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Scheduling;

[TestFixture]
public class DirectSourcePlayoutBuilderTests
{
    private IMediaCollectionRepository _mediaCollectionRepository;
    private ILogger<DirectSourcePlayoutBuilder> _logger;
    private DirectSourcePlayoutBuilder _builder;

    [SetUp]
    public void SetUp()
    {
        _mediaCollectionRepository = Substitute.For<IMediaCollectionRepository>();
        _logger = Substitute.For<ILogger<DirectSourcePlayoutBuilder>>();
        _builder = new DirectSourcePlayoutBuilder(_mediaCollectionRepository, _logger);
    }

    [Test]
    public async Task Build_Should_Return_Empty_When_SourceId_Is_Null()
    {
        var playout = new Playout
        {
            Id = 1,
            SourceId = null
        };

        var referenceData = new PlayoutReferenceData(new Channel(Guid.NewGuid()), [], null, [], [], TimeSpan.Zero);

        var result = await _builder.Build(
            DateTimeOffset.UtcNow,
            playout,
            referenceData,
            PlayoutBuildMode.Continue,
            CancellationToken.None);

        result.IsRight.ShouldBeTrue();
        foreach (PlayoutBuildResult buildResult in result.RightToSeq())
        {
            buildResult.AddedItems.ShouldBeEmpty();
        }
    }

    [Test]
    public async Task Build_Should_Generate_Continuous_Items_Until_TargetEnd()
    {
        var movie1 = new Movie
        {
            Id = 101,
            MediaVersions = new List<MediaVersion> { new() { Duration = TimeSpan.FromHours(1) } }
        };
        var movie2 = new Movie
        {
            Id = 102,
            MediaVersions = new List<MediaVersion> { new() { Duration = TimeSpan.FromHours(2) } }
        };

        var items = new List<MediaItem> { movie1, movie2 };
        _mediaCollectionRepository.GetItems(42).Returns(items);

        var playout = new Playout
        {
            Id = 2,
            SourceId = 42,
            SourceKind = ProgramScheduleSourceKind.Collection,
            DeliveryMode = PlayoutDeliveryMode.Loop,
            DaysToBuild = 1 // 24 horas
        };

        var start = new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
        var referenceData = new PlayoutReferenceData(new Channel(Guid.NewGuid()), [], null, [], [], TimeSpan.Zero);

        var result = await _builder.Build(
            start,
            playout,
            referenceData,
            PlayoutBuildMode.Reset,
            CancellationToken.None);

        result.IsRight.ShouldBeTrue();
        foreach (PlayoutBuildResult buildResult in result.RightToSeq())
        {
            buildResult.AddedItems.Count.ShouldBeGreaterThan(0);
            buildResult.ClearItems.ShouldBeTrue();

            // Total de horas deve cobrir pelo menos 24h
            var totalDuration = buildResult.AddedItems.Last().Finish - start.UtcDateTime;
            totalDuration.TotalHours.ShouldBeGreaterThanOrEqualTo(24);

            // Continuidade temporal: cada item começa exatamente quando o anterior termina
            for (int i = 1; i < buildResult.AddedItems.Count; i++)
            {
                buildResult.AddedItems[i].Start.ShouldBe(buildResult.AddedItems[i - 1].Finish);
            }
        }
    }

    [Test]
    public async Task Build_Should_Stop_After_One_Pass_When_DeliveryMode_Is_PlayOnce()
    {
        var movie1 = new Movie
        {
            Id = 201,
            MediaVersions = new List<MediaVersion> { new() { Duration = TimeSpan.FromHours(1) } }
        };
        var movie2 = new Movie
        {
            Id = 202,
            MediaVersions = new List<MediaVersion> { new() { Duration = TimeSpan.FromHours(1) } }
        };

        var items = new List<MediaItem> { movie1, movie2 };
        _mediaCollectionRepository.GetItems(50).Returns(items);

        var playout = new Playout
        {
            Id = 3,
            SourceId = 50,
            SourceKind = ProgramScheduleSourceKind.Collection,
            DeliveryMode = PlayoutDeliveryMode.PlayOnce,
            DaysToBuild = 5
        };

        var start = new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);
        var referenceData = new PlayoutReferenceData(new Channel(Guid.NewGuid()), [], null, [], [], TimeSpan.Zero);

        var result = await _builder.Build(
            start,
            playout,
            referenceData,
            PlayoutBuildMode.Continue,
            CancellationToken.None);

        result.IsRight.ShouldBeTrue();
        foreach (PlayoutBuildResult buildResult in result.RightToSeq())
        {
            // No modo PlayOnce, apenas 2 itens devem ser adicionados (sem looping infinito)
            buildResult.AddedItems.Count.ShouldBe(2);
            buildResult.AddedItems[0].MediaItemId.ShouldBe(201);
            buildResult.AddedItems[1].MediaItemId.ShouldBe(202);
        }
    }
}
