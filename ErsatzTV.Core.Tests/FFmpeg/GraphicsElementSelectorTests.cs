using ErsatzTV.Core.Domain;
using ErsatzTV.Core.FFmpeg;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.FFmpeg;

[TestFixture]
public class GraphicsElementSelectorTests
{
    private static readonly GraphicsElementSelector GraphicsElementSelector =
        new(NullLogger<GraphicsElementSelector>.Instance);

    private static readonly DateTimeOffset Now = new(2025, 08, 17, 12, 0, 0, TimeSpan.FromHours(-5));

    [Test]
    public void HlsDirect_Should_Return_No_Graphics()
    {
        var channel = new Channel(Guid.NewGuid()) { StreamingMode = StreamingMode.HttpLiveStreamingDirect };
        var playoutItem = new PlayoutItem
        {
            PlayoutItemGraphicsElements =
            [
                new PlayoutItemGraphicsElement { GraphicsElement = new GraphicsElement { Id = 1, Path = "GE1" } }
            ]
        };

        List<PlayoutItemGraphicsElement> result = GraphicsElementSelector.SelectGraphicsElements(
            channel,
            playoutItem,
            Now,
            shouldLogMessages: false);

        result.ShouldBeEmpty();
    }

    [Test]
    public void NonHlsDirect_Should_Return_PlayoutItem_Graphics()
    {
        var channel = new Channel(Guid.NewGuid()) { StreamingMode = StreamingMode.TransportStreamHybrid };
        var graphicsElement = new GraphicsElement { Id = 1, Path = "GE1" };
        var playoutItem = new PlayoutItem
        {
            PlayoutItemGraphicsElements =
            [
                new PlayoutItemGraphicsElement { GraphicsElement = graphicsElement }
            ]
        };

        List<PlayoutItemGraphicsElement> result = GraphicsElementSelector.SelectGraphicsElements(
            channel,
            playoutItem,
            Now,
            shouldLogMessages: false);

        result.Count.ShouldBe(1);
        result[0].GraphicsElement.ShouldBe(graphicsElement);
    }
}
