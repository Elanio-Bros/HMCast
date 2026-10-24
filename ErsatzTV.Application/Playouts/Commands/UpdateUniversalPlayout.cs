using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Scheduling;
using MediatR;

namespace ErsatzTV.Application.Playouts;

public record UpdateUniversalPlayout(
    int PlayoutId,
    ProgramScheduleSourceKind SourceKind,
    int? SourceId,
    string ScheduleFile,
    PlayoutDeliveryMode DeliveryMode,
    int DaysToBuild,
    int? ScreenLayoutId,
    PlayoutCalendarMode CalendarMode,
    List<PlayoutCalendarRuleDto> CalendarRules,
    bool IsEnabled = true
) : IRequest<Either<BaseError, Unit>>;
