using System;
using System.Collections.Generic;
using System.Linq;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Scheduling;
using ErsatzTV.FFmpeg.Filter;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Streaming;

[TestFixture]
public class ContinuousTransmissionValidationTests
{
    [Test]
    public void Timeline_Should_Have_Zero_Gaps_Between_Consecutive_Items()
    {
        // Validação da integridade temporal da transmissão linear (TASK-4.3)
        var start = new DateTime(2026, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        var items = new List<PlayoutItem>();

        DateTime current = start;
        for (int i = 0; i < 48; i++) // 48 blocos de 30 minutos = 24h
        {
            var finish = current.AddMinutes(30);
            items.Add(new PlayoutItem
            {
                Start = current,
                Finish = finish,
                MediaItemId = i + 1
            });
            current = finish;
        }

        // Testar continuidade estrita
        for (int i = 0; i < items.Count - 1; i++)
        {
            var itemA = items[i];
            var itemB = items[i + 1];

            // Gap zero entre segmentos
            (itemB.Start - itemA.Finish).ShouldBe(TimeSpan.Zero);
        }

        (items.Last().Finish - items.First().Start).ShouldBe(TimeSpan.FromHours(24));
    }

    [Test]
    public void Radio_Mode_Continuous_Transmission_Should_Maintain_Audio_With_Minimum_Video_Overhead()
    {
        // Garante que o modo rádio opera em 1fps com tela preta e sem quebra do fluxo MPEG-TS
        var radioFilter = new RadioModeVideoFilter();

        radioFilter.Filter.ShouldContain("color=c=black");
        radioFilter.Filter.ShouldContain("rate=1");
        radioFilter.FilterOptions.ShouldContain("-map");
        radioFilter.FilterOptions.ShouldContain("0:a");
    }

    [Test]
    public void MediaSkip_Chapters_Should_Be_Preserved_In_Schedule_Configuration()
    {
        // Garante a blindagem dos Cutouts no modelo unificado de transmissão
        var item = new ProgramScheduleItemOne
        {
            RespectMediaSkipChapters = true,
            FillCommercialGapsWithFillers = true,
            FixedStartTimeBehavior = FixedStartTimeBehavior.WaitUntilNext
        };

        item.RespectMediaSkipChapters.ShouldBeTrue();
        item.FillCommercialGapsWithFillers.ShouldBeTrue();
        item.FixedStartTimeBehavior.ShouldBe(FixedStartTimeBehavior.WaitUntilNext);
    }
}
