using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Scheduling;
using MediatR;

namespace ErsatzTV.Application.Playouts;

public class PlayoutCalendarRuleDto
{
    public int Index { get; set; }
    public CalendarDayOfWeek DaysOfWeek { get; set; } = CalendarDayOfWeek.All;
    public DateTimeOffset? StartDate { get; set; }
    public DateTimeOffset? EndDate { get; set; }
    public int? RecurringStartMonth { get; set; }
    public int? RecurringStartDay { get; set; }
    public int? RecurringEndMonth { get; set; }
    public int? RecurringEndDay { get; set; }
    public TimeSpan? DailyStartTime { get; set; }
    public TimeSpan? DailyEndTime { get; set; }
}

public record CreateUniversalPlayout(
    int ChannelId,
    ProgramScheduleSourceKind SourceKind,
    int? SourceId,
    string ScheduleFile,
    PlayoutDeliveryMode DeliveryMode,
    int DaysToBuild,
    int? ScreenLayoutId,
    PlayoutCalendarMode CalendarMode,
    List<PlayoutCalendarRuleDto> CalendarRules,
    bool IsEnabled = true
) : IRequest<Either<BaseError, CreatePlayoutResponse>>;

public record TogglePlayoutEnabled(int PlayoutId, bool IsEnabled)
    : IRequest<Either<BaseError, Unit>>;
