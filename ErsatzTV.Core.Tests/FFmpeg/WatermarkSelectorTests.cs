using ErsatzTV.Core.Domain;
using ErsatzTV.Core.FFmpeg;
using ErsatzTV.Core.Interfaces.Images;
using Microsoft.Extensions.Logging;
using NSubstitute;
using NUnit.Framework;
using Serilog;
using Shouldly;
using Testably.Abstractions.Testing;

namespace ErsatzTV.Core.Tests.FFmpeg;

[TestFixture]
public class WatermarkSelectorTests
{
    private static readonly WatermarkSelector WatermarkSelector;
    private static readonly Option<ChannelWatermark> WatermarkNone;
    private static readonly ChannelWatermark WatermarkGlobal;
    private static readonly ChannelWatermark WatermarkChannel;
    private static readonly ChannelWatermark WatermarkPlayoutItem;
    private static readonly Channel ChannelWithWatermark;
    private static readonly Channel ChannelNoWatermark;
    private static readonly DateTimeOffset Now = new(2025, 08, 17, 12, 0, 0, TimeSpan.FromHours(-5));

    private static readonly PlayoutItem PlayoutItemDisableWatermarks =
        new() { Watermarks = [], DisableWatermarks = true };

    private static readonly PlayoutItem PlayoutItemWithNoWatermarks =
        new() { Watermarks = [], DisableWatermarks = false };

    private static readonly PlayoutItem PlayoutItemWithWatermark;
    private static readonly PlayoutItem PlayoutItemWithDisabledWatermark;

    private static readonly List<ChannelWatermark> WatermarkResultEmpty = [];

    static WatermarkSelectorTests()
    {
        Log.Logger = new LoggerConfiguration()
            .MinimumLevel.Debug()
            .WriteTo.Console()
            .CreateLogger();

        var loggerFactory = new LoggerFactory().AddSerilog(Log.Logger);

        // watermarks should always exist; effectively ignoring filesystem checks for now
        var mockFileSystem = new MockFileSystem();
        mockFileSystem.Initialize()
            .WithFile("/tmp/watermark");

        var fakeImageCache = Substitute.For<IImageCache>();
        fakeImageCache.GetPathForImage(Arg.Any<string>(), Arg.Is(ArtworkKind.Watermark), Arg.Any<Option<int>>())
            .Returns(_ => "/tmp/watermark");

        WatermarkSelector = new WatermarkSelector(
            mockFileSystem,
            fakeImageCache,
            loggerFactory.CreateLogger<WatermarkSelector>());

        WatermarkNone = Option<ChannelWatermark>.None;

        WatermarkGlobal = new ChannelWatermark { Id = 0, Name = "Global", Image = "GlobalImage" };
        WatermarkChannel = new ChannelWatermark { Id = 1, Name = "Channel", Image = "ChannelImage" };
        WatermarkPlayoutItem = new ChannelWatermark { Id = 2, Name = "PlayoutItem", Image = "PlayoutItemImage" };

        ChannelWithWatermark = new Channel(Guid.Empty)
            { Id = 0, Watermark = WatermarkChannel, WatermarkId = WatermarkChannel.Id };

        ChannelNoWatermark = new Channel(Guid.Empty) { Id = 0, Watermark = null, WatermarkId = null };

        PlayoutItemWithWatermark = new PlayoutItem { Watermarks = [WatermarkPlayoutItem], DisableWatermarks = false };

        PlayoutItemWithDisabledWatermark = new PlayoutItem
        {
            Watermarks = [WatermarkPlayoutItem],
            DisableWatermarks = true
        };
    }

    private static IEnumerable<(Option<ChannelWatermark>, Channel, PlayoutItem, List<ChannelWatermark>)>
        SelectWatermarksTestCases()
    {
        // no watermark when none are configured
        yield return (WatermarkNone, ChannelNoWatermark, PlayoutItemWithNoWatermarks, WatermarkResultEmpty);

        // no watermark when global configured but disabled playout item
        yield return (WatermarkGlobal, ChannelNoWatermark, PlayoutItemDisableWatermarks, WatermarkResultEmpty);

        // global watermark when global configured
        yield return (WatermarkGlobal, ChannelNoWatermark, PlayoutItemWithNoWatermarks, [WatermarkGlobal]);

        // channel watermark when global and channel configured
        yield return (WatermarkGlobal, ChannelWithWatermark, PlayoutItemWithNoWatermarks, [WatermarkChannel]);

        // channel watermark when channel configured
        yield return (WatermarkNone, ChannelWithWatermark, PlayoutItemWithNoWatermarks, [WatermarkChannel]);

        // playout item when global, channel and playout item configured
        yield return (WatermarkGlobal, ChannelWithWatermark, PlayoutItemWithWatermark, [WatermarkPlayoutItem]);

        // playout item when channel and playout item configured
        yield return (WatermarkNone, ChannelWithWatermark, PlayoutItemWithWatermark, [WatermarkPlayoutItem]);

        // playout item when playout item configured
        yield return (WatermarkNone, ChannelNoWatermark, PlayoutItemWithWatermark, [WatermarkPlayoutItem]);

        // no watermark when channel configured with playout item disabled
        yield return (WatermarkNone, ChannelWithWatermark, PlayoutItemDisableWatermarks, WatermarkResultEmpty);

        // no watermark when global and channel configured with playout item disabled
        yield return (WatermarkGlobal, ChannelWithWatermark, PlayoutItemDisableWatermarks, WatermarkResultEmpty);

        // no watermark when global, channel and playout item configured with playout item disabled
        yield return (WatermarkGlobal, ChannelWithWatermark, PlayoutItemWithDisabledWatermark, WatermarkResultEmpty);
    }

    [TestCaseSource(nameof(SelectWatermarksTestCases))]
    public void Should_Select_Appropriate_Watermark(
        (Option<ChannelWatermark> globalWatermark,
        Channel channel,
        PlayoutItem playoutItem,
        List<ChannelWatermark> expectedWatermarks) td)
    {
        List<WatermarkOptions> watermarks = WatermarkSelector.SelectWatermarks(
            td.globalWatermark,
            td.channel,
            td.playoutItem,
            Now,
            shouldLogMessages: true);

        watermarks.Count.ShouldBe(td.expectedWatermarks.Count);
        for (var i = 0; i < td.expectedWatermarks.Count; i++)
        {
            watermarks[i].Watermark.ShouldBe(td.expectedWatermarks[i]);
        }
    }
}
