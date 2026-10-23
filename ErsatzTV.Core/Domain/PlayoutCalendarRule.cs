using System;

namespace ErsatzTV.Core.Domain;

public class PlayoutCalendarRule
{
    public int Id { get; set; }

    public int PlayoutId { get; set; }
    public Playout Playout { get; set; }

    // Ordem/Prioridade da regra
    public int Index { get; set; }

    // Bitmask para dias da semana
    public CalendarDayOfWeek DaysOfWeek { get; set; } = CalendarDayOfWeek.All;

    // Faixa de datas específica com ano
    public DateTimeOffset? StartDate { get; set; }
    public DateTimeOffset? EndDate { get; set; }

    // Faixa sazonal recorrente sem ano (mês e dia)
    public int? RecurringStartMonth { get; set; }
    public int? RecurringStartDay { get; set; }
    public int? RecurringEndMonth { get; set; }
    public int? RecurringEndDay { get; set; }

    // Janela diária de horários opcionais para este playout
    public TimeSpan? DailyStartTime { get; set; }
    public TimeSpan? DailyEndTime { get; set; }
}
