using System;
using System.Collections.Generic;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Scheduling;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Scheduling;

[TestFixture]
public class PlayoutCalendarEvaluatorTests
{
    private PlayoutCalendarEvaluator _evaluator;

    [SetUp]
    public void SetUp()
    {
        _evaluator = new PlayoutCalendarEvaluator();
    }

    [Test]
    public void Disabled_Playout_Should_Return_Disabled()
    {
        var playout = new Playout { IsEnabled = false };
        var status = _evaluator.GetPlayoutStatus(playout, DateTimeOffset.UtcNow);

        status.ShouldBe(PlayoutRuntimeStatus.Disabled);
        _evaluator.IsPlayoutActive(playout, DateTimeOffset.UtcNow).ShouldBeFalse();
    }

    [Test]
    public void AlwaysActive_Playout_Should_Return_ActiveInTransmission()
    {
        var playout = new Playout
        {
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.AlwaysActive
        };

        var status = _evaluator.GetPlayoutStatus(playout, DateTimeOffset.UtcNow);

        status.ShouldBe(PlayoutRuntimeStatus.ActiveInTransmission);
        _evaluator.IsPlayoutActive(playout, DateTimeOffset.UtcNow).ShouldBeTrue();
    }

    [Test]
    public void Playout_With_Future_StartDate_Should_Return_ScheduledFuture()
    {
        var now = new DateTimeOffset(2026, 6, 1, 12, 0, 0, TimeSpan.Zero);
        var playout = new Playout
        {
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.DateRange,
            CalendarRules = new List<PlayoutCalendarRule>
            {
                new()
                {
                    StartDate = new DateTimeOffset(2026, 7, 1, 0, 0, 0, TimeSpan.Zero),
                    EndDate = new DateTimeOffset(2026, 7, 31, 23, 59, 59, TimeSpan.Zero)
                }
            }
        };

        var status = _evaluator.GetPlayoutStatus(playout, now);
        status.ShouldBe(PlayoutRuntimeStatus.ScheduledFuture);
        _evaluator.IsPlayoutActive(playout, now).ShouldBeFalse();
    }

    [Test]
    public void Playout_With_Past_EndDate_Should_Return_OutOfPeriod()
    {
        var now = new DateTimeOffset(2026, 8, 1, 12, 0, 0, TimeSpan.Zero);
        var playout = new Playout
        {
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.DateRange,
            CalendarRules = new List<PlayoutCalendarRule>
            {
                new()
                {
                    StartDate = new DateTimeOffset(2026, 7, 1, 0, 0, 0, TimeSpan.Zero),
                    EndDate = new DateTimeOffset(2026, 7, 31, 23, 59, 59, TimeSpan.Zero)
                }
            }
        };

        var status = _evaluator.GetPlayoutStatus(playout, now);
        status.ShouldBe(PlayoutRuntimeStatus.OutOfPeriod);
        _evaluator.IsPlayoutActive(playout, now).ShouldBeFalse();
    }

    [Test]
    public void Playout_With_Active_DateRange_Should_Return_ActiveInTransmission()
    {
        var now = new DateTimeOffset(2026, 7, 15, 12, 0, 0, TimeSpan.Zero);
        var playout = new Playout
        {
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.DateRange,
            CalendarRules = new List<PlayoutCalendarRule>
            {
                new()
                {
                    StartDate = new DateTimeOffset(2026, 7, 1, 0, 0, 0, TimeSpan.Zero),
                    EndDate = new DateTimeOffset(2026, 7, 31, 23, 59, 59, TimeSpan.Zero),
                    DaysOfWeek = CalendarDayOfWeek.All
                }
            }
        };

        var status = _evaluator.GetPlayoutStatus(playout, now);
        status.ShouldBe(PlayoutRuntimeStatus.ActiveInTransmission);
        _evaluator.IsPlayoutActive(playout, now).ShouldBeTrue();
    }

    [Test]
    public void Playout_With_DayOfWeek_Mismatch_Should_Return_OutOfPeriod()
    {
        // 2026-07-15 foi uma Quarta-feira (Wednesday)
        var wednesday = new DateTimeOffset(2026, 7, 15, 12, 0, 0, TimeSpan.Zero);
        wednesday.DayOfWeek.ShouldBe(DayOfWeek.Wednesday);

        var playout = new Playout
        {
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.SpecificDaysOfWeek,
            CalendarRules = new List<PlayoutCalendarRule>
            {
                new()
                {
                    // Apenas finais de semana
                    DaysOfWeek = CalendarDayOfWeek.Saturday | CalendarDayOfWeek.Sunday
                }
            }
        };

        var status = _evaluator.GetPlayoutStatus(playout, wednesday);
        status.ShouldBe(PlayoutRuntimeStatus.OutOfPeriod);
    }

    [Test]
    public void Playout_With_DailyTimeWindow_Should_Match_TimeOfDay()
    {
        // 14:30 UTC
        var now = new DateTimeOffset(2026, 7, 15, 14, 30, 0, TimeSpan.Zero);

        var playout = new Playout
        {
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.CustomRules,
            CalendarRules = new List<PlayoutCalendarRule>
            {
                new()
                {
                    DailyStartTime = new TimeSpan(14, 0, 0),
                    DailyEndTime = new TimeSpan(18, 0, 0),
                    DaysOfWeek = CalendarDayOfWeek.All
                }
            }
        };

        var status = _evaluator.GetPlayoutStatus(playout, now);
        status.ShouldBe(PlayoutRuntimeStatus.ActiveInTransmission);

        // Fora da janela: 19:00 UTC
        var later = new DateTimeOffset(2026, 7, 15, 19, 0, 0, TimeSpan.Zero);
        _evaluator.GetPlayoutStatus(playout, later).ShouldBe(PlayoutRuntimeStatus.OutOfPeriod);
    }

    [Test]
    public void SelectActivePlayout_Should_Prioritize_Specific_Rules_Over_AlwaysActive()
    {
        var now = new DateTimeOffset(2026, 12, 25, 20, 0, 0, TimeSpan.Zero);

        var genericPlayout = new Playout
        {
            Id = 1,
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.AlwaysActive
        };

        var holidayPlayout = new Playout
        {
            Id = 2,
            IsEnabled = true,
            CalendarMode = PlayoutCalendarMode.CustomRules,
            CalendarRules = new List<PlayoutCalendarRule>
            {
                new()
                {
                    StartDate = new DateTimeOffset(2026, 12, 24, 0, 0, 0, TimeSpan.Zero),
                    EndDate = new DateTimeOffset(2026, 12, 26, 23, 59, 59, TimeSpan.Zero),
                    DaysOfWeek = CalendarDayOfWeek.All
                }
            }
        };

        var playouts = new List<Playout> { genericPlayout, holidayPlayout };
        var selected = _evaluator.SelectActivePlayout(playouts, now);

        selected.IsSome.ShouldBeTrue();
        foreach (Playout p in selected)
        {
            // O playout com regras customizadas tem maior especificidade e deve vencer o AlwaysActive
            p.Id.ShouldBe(2);
        }
    }
}
