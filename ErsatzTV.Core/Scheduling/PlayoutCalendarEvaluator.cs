using System;
using System.Collections.Generic;
using System.Linq;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Interfaces.Scheduling;
using LanguageExt;

namespace ErsatzTV.Core.Scheduling;

public class PlayoutCalendarEvaluator : IPlayoutCalendarEvaluator
{
    public bool IsPlayoutActive(Playout playout, DateTimeOffset currentTime) =>
        GetPlayoutStatus(playout, currentTime) == PlayoutRuntimeStatus.ActiveInTransmission;

    public PlayoutRuntimeStatus GetPlayoutStatus(Playout playout, DateTimeOffset currentTime)
    {
        if (playout is null || !playout.IsEnabled)
        {
            return PlayoutRuntimeStatus.Disabled;
        }

        if (playout.CalendarMode == PlayoutCalendarMode.AlwaysActive)
        {
            return PlayoutRuntimeStatus.ActiveInTransmission;
        }

        if (playout.CalendarRules is null || playout.CalendarRules.Count == 0)
        {
            return PlayoutRuntimeStatus.ActiveInTransmission;
        }

        bool hasFuture = false;

        foreach (PlayoutCalendarRule rule in playout.CalendarRules)
        {
            // 1. Faixa de datas específica com ano
            if (rule.StartDate.HasValue && currentTime < rule.StartDate.Value)
            {
                hasFuture = true;
                continue;
            }

            if (rule.EndDate.HasValue && currentTime > rule.EndDate.Value)
            {
                continue;
            }

            // 2. Dias da semana (Bitmask)
            var dayFlag = (CalendarDayOfWeek)(1 << (int)currentTime.DayOfWeek);
            if ((rule.DaysOfWeek & dayFlag) == 0)
            {
                continue;
            }

            // 3. Faixa sazonal recorrente sem ano
            if (rule.RecurringStartMonth.HasValue && rule.RecurringStartDay.HasValue)
            {
                var start = new DateTime(currentTime.Year, rule.RecurringStartMonth.Value, rule.RecurringStartDay.Value);
                int endYear = currentTime.Year;
                int endMonth = rule.RecurringEndMonth ?? rule.RecurringStartMonth.Value;
                int endDay = rule.RecurringEndDay ?? rule.RecurringStartDay.Value;

                if (endMonth < rule.RecurringStartMonth.Value)
                {
                    endYear++;
                }

                var end = new DateTime(endYear, endMonth, endDay, 23, 59, 59);
                DateTime currentDt = currentTime.LocalDateTime;

                if (currentDt < start)
                {
                    hasFuture = true;
                    continue;
                }

                if (currentDt > end)
                {
                    continue;
                }
            }

            // 4. Janela de horários diários
            TimeSpan timeOfDay = currentTime.TimeOfDay;
            if (rule.DailyStartTime.HasValue && timeOfDay < rule.DailyStartTime.Value)
            {
                hasFuture = true;
                continue;
            }

            if (rule.DailyEndTime.HasValue && timeOfDay > rule.DailyEndTime.Value)
            {
                continue;
            }

            // Atendeu a todos os critérios da regra
            return PlayoutRuntimeStatus.ActiveInTransmission;
        }

        return hasFuture ? PlayoutRuntimeStatus.ScheduledFuture : PlayoutRuntimeStatus.OutOfPeriod;
    }

    public Option<Playout> SelectActivePlayout(IEnumerable<Playout> channelPlayouts, DateTimeOffset currentTime)
    {
        if (channelPlayouts is null)
        {
            return Option<Playout>.None;
        }

        List<Playout> active = channelPlayouts
            .Where(p => IsPlayoutActive(p, currentTime))
            .ToList();

        if (active.Count == 0)
        {
            return Option<Playout>.None;
        }

        // Prioridade de seleção: CustomRules > DateRange > RecurringAnnual > SpecificDaysOfWeek > AlwaysActive
        Playout selected = active
            .OrderByDescending(p => p.CalendarMode switch
            {
                PlayoutCalendarMode.CustomRules => 5,
                PlayoutCalendarMode.DateRange => 4,
                PlayoutCalendarMode.RecurringAnnual => 3,
                PlayoutCalendarMode.SpecificDaysOfWeek => 2,
                _ => 1
            })
            .FirstOrDefault();

        return Optional(selected);
    }
}
