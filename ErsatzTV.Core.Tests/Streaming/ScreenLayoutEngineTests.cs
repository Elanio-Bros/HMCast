using System;
using System.Collections.Generic;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Interfaces.Streaming;
using ErsatzTV.Core.Streaming;
using Microsoft.Extensions.Logging;
using NSubstitute;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Streaming;

[TestFixture]
public class ScreenLayoutEngineTests
{
    private ILogger<ScreenLayoutEngine> _logger;
    private ScreenLayoutEngine _engine;

    [SetUp]
    public void SetUp()
    {
        _logger = Substitute.For<ILogger<ScreenLayoutEngine>>();
        _engine = new ScreenLayoutEngine(_logger);
    }

    [Test]
    public void ResolveActiveLayout_Should_Prioritize_Playout_Over_Channel()
    {
        var channelLayout = new ScreenLayout { Id = 1, Name = "Channel Layout" };
        var playoutLayout = new ScreenLayout { Id = 2, Name = "Playout Layout" };

        var channel = new Channel(Guid.NewGuid()) { ScreenLayout = channelLayout };
        var playout = new Playout { ScreenLayout = playoutLayout };

        var resolved = _engine.ResolveActiveLayout(playout, channel);

        resolved.IsSome.ShouldBeTrue();
        foreach (ScreenLayout sl in resolved)
        {
            sl.Id.ShouldBe(2);
            sl.Name.ShouldBe("Playout Layout");
        }
    }

    [Test]
    public void ResolveActiveLayout_Should_Fallback_To_Channel_When_Playout_Has_No_Layout()
    {
        var channelLayout = new ScreenLayout { Id = 1, Name = "Channel Layout" };

        var channel = new Channel(Guid.NewGuid()) { ScreenLayout = channelLayout };
        var playout = new Playout { ScreenLayout = null };

        var resolved = _engine.ResolveActiveLayout(playout, channel);

        resolved.IsSome.ShouldBeTrue();
        foreach (ScreenLayout sl in resolved)
        {
            sl.Id.ShouldBe(1);
        }
    }

    [Test]
    public void GenerateFilterSteps_Should_Return_Empty_When_Layout_Has_No_Elements()
    {
        var layout = new ScreenLayout { Elements = new List<ScreenLayoutElement>() };
        var playoutItem = new PlayoutItem { Start = DateTime.UtcNow, Finish = DateTime.UtcNow.AddMinutes(30) };

        ScreenLayoutFilterResult result = _engine.GenerateFilterSteps(
            layout,
            playoutItem,
            DateTimeOffset.UtcNow,
            1920,
            1080);

        result.FilterComplexSteps.ShouldBeEmpty();
        result.AdditionalInputs.ShouldBeEmpty();
    }

    [Test]
    public void GenerateFilterSteps_Should_Generate_Overlay_For_LogoWatermark()
    {
        var layout = new ScreenLayout
        {
            Elements = new List<ScreenLayoutElement>
            {
                new()
                {
                    Id = 1,
                    Name = "Logo Top Right",
                    ElementType = ScreenLayoutElementType.LogoWatermark,
                    ContentPath = "/media/logos/channel_logo.png",
                    X = 0.9,
                    Y = 0.05,
                    Opacity = 0.85
                }
            }
        };

        var now = DateTimeOffset.UtcNow;
        var playoutItem = new PlayoutItem
        {
            Start = now.AddMinutes(-5).UtcDateTime,
            Finish = now.AddMinutes(25).UtcDateTime
        };

        ScreenLayoutFilterResult result = _engine.GenerateFilterSteps(
            layout,
            playoutItem,
            now,
            1920,
            1080);

        result.AdditionalInputs.ShouldContain("/media/logos/channel_logo.png");
        result.FilterComplexSteps.Count.ShouldBe(1);

        // 0.9 * 1920 = 1728; 0.05 * 1080 = 54
        result.FilterComplexSteps[0].ShouldContain("overlay=x=1728:y=54");
    }

    [Test]
    public void GenerateFilterSteps_Should_Generate_DrawText_For_TextBanner()
    {
        var layout = new ScreenLayout
        {
            Elements = new List<ScreenLayoutElement>
            {
                new()
                {
                    Id = 2,
                    Name = "News Ticker",
                    ElementType = ScreenLayoutElementType.TextBanner,
                    TextContent = "Breaking News: HMCast 3.0 Live",
                    X = 50,
                    Y = 1000,
                    Opacity = 1.0
                }
            }
        };

        var now = DateTimeOffset.UtcNow;
        var playoutItem = new PlayoutItem
        {
            Start = now.AddMinutes(-2).UtcDateTime,
            Finish = now.AddMinutes(28).UtcDateTime
        };

        ScreenLayoutFilterResult result = _engine.GenerateFilterSteps(
            layout,
            playoutItem,
            now,
            1920,
            1080);

        result.FilterComplexSteps.Count.ShouldBe(1);
        result.FilterComplexSteps[0].ShouldContain("drawtext=text='Breaking News\\: HMCast 3.0 Live'");
        result.FilterComplexSteps[0].ShouldContain("x=50:y=1000");
    }

    [Test]
    public void GenerateFilterSteps_Should_Honor_Rule_Hide_On_CommercialBreak()
    {
        var element = new ScreenLayoutElement
        {
            Id = 3,
            Name = "Persistent Logo",
            ElementType = ScreenLayoutElementType.LogoWatermark,
            ContentPath = "/media/logo.png",
            X = 100,
            Y = 100
        };

        var rule = new ScreenLayoutRule
        {
            Id = 1,
            ElementId = 3,
            Trigger = ScreenLayoutRuleTrigger.CommercialBreak,
            Action = ScreenLayoutRuleAction.Hide
        };

        var layout = new ScreenLayout
        {
            Elements = new List<ScreenLayoutElement> { element },
            Rules = new List<ScreenLayoutRule> { rule }
        };

        var now = DateTimeOffset.UtcNow;

        // Playout item é comercial (FillerKind != None)
        var commercialItem = new PlayoutItem
        {
            Start = now.AddMinutes(-1).UtcDateTime,
            Finish = now.AddMinutes(1).UtcDateTime,
            FillerKind = FillerKind.MidRoll
        };

        ScreenLayoutFilterResult result = _engine.GenerateFilterSteps(
            layout,
            commercialItem,
            now,
            1920,
            1080);

        // O elemento deve ser ocultado durante o intervalo comercial
        result.FilterComplexSteps.ShouldBeEmpty();
        result.AdditionalInputs.ShouldBeEmpty();
    }

    [Test]
    public void GenerateFilterSteps_Should_Honor_Rule_Show_On_ProgramStart()
    {
        var element = new ScreenLayoutElement
        {
            Id = 4,
            Name = "Intro Graphic",
            ElementType = ScreenLayoutElementType.LogoWatermark,
            ContentPath = "/media/intro.png",
            X = 200,
            Y = 200
        };

        var rule = new ScreenLayoutRule
        {
            Id = 2,
            ElementId = 4,
            Trigger = ScreenLayoutRuleTrigger.ProgramStart,
            Action = ScreenLayoutRuleAction.Show,
            OffsetSeconds = 10,
            DurationSeconds = 15
        };

        var layout = new ScreenLayout
        {
            Elements = new List<ScreenLayoutElement> { element },
            Rules = new List<ScreenLayoutRule> { rule }
        };

        var now = DateTimeOffset.UtcNow;
        var playoutItem = new PlayoutItem
        {
            Start = now.AddSeconds(-5).UtcDateTime,
            Finish = now.AddMinutes(30).UtcDateTime,
            FillerKind = FillerKind.None
        };

        ScreenLayoutFilterResult result = _engine.GenerateFilterSteps(
            layout,
            playoutItem,
            now,
            1920,
            1080);

        result.FilterComplexSteps.Count.ShouldBe(1);
        result.FilterComplexSteps[0].ShouldContain(":enable='between(t,10.0,25.0)'");
    }
}
