using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;
using static LanguageExt.Prelude;

namespace ErsatzTV.Application.Playouts;

public class GetUniversalPlayoutByIdHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetUniversalPlayoutById, Option<UniversalPlayoutViewModel>>
{
    public async Task<Option<UniversalPlayoutViewModel>> Handle(
        GetUniversalPlayoutById request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        Playout playout = await dbContext.Playouts
            .Include(p => p.Channel)
            .Include(p => p.CalendarRules)
            .AsNoTracking()
            .FirstOrDefaultAsync(p => p.Id == request.PlayoutId, cancellationToken);

        if (playout == null)
        {
            return Option<UniversalPlayoutViewModel>.None;
        }

        var calendarRules = playout.CalendarRules.OrderBy(r => r.Index).Select(r => new PlayoutCalendarRuleDto
        {
            Index = r.Index,
            DaysOfWeek = r.DaysOfWeek,
            StartDate = r.StartDate,
            EndDate = r.EndDate,
            RecurringStartMonth = r.RecurringStartMonth,
            RecurringStartDay = r.RecurringStartDay,
            RecurringEndMonth = r.RecurringEndMonth,
            RecurringEndDay = r.RecurringEndDay,
            DailyStartTime = r.DailyStartTime,
            DailyEndTime = r.DailyEndTime
        }).ToList();

        return new UniversalPlayoutViewModel(
            playout.Id,
            playout.ChannelId,
            playout.Channel?.Name ?? string.Empty,
            playout.Channel?.Number ?? string.Empty,
            playout.SourceKind,
            playout.SourceId ?? playout.ProgramScheduleId,
            playout.ScheduleFile,
            playout.DeliveryMode,
            playout.DaysToBuild,
            playout.ScreenLayoutId,
            playout.CalendarMode,
            calendarRules,
            playout.IsEnabled
        );
    }
}
