using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Scheduling;

namespace ErsatzTV.Application.Playouts;

public record UniversalPlayoutViewModel(
    int PlayoutId,
    int ChannelId,
    string ChannelName,
    string ChannelNumber,
    ProgramScheduleSourceKind SourceKind,
    int? SourceId,
    string ScheduleFile,
    PlayoutDeliveryMode DeliveryMode,
    int DaysToBuild,
    int? ScreenLayoutId,
    PlayoutCalendarMode CalendarMode,
    List<PlayoutCalendarRuleDto> CalendarRules,
    bool IsEnabled
);
