using System.Threading.Channels;
using ErsatzTV.Application.Channels;
using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Scheduling;
using ErsatzTV.Core.Scheduling;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.Playouts;

public class UpdateUniversalPlayoutHandler(
    ChannelWriter<IBackgroundServiceRequest> workerChannel,
    IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdateUniversalPlayout, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(
        UpdateUniversalPlayout request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        Playout playout = await dbContext.Playouts
            .Include(p => p.CalendarRules)
            .FirstOrDefaultAsync(p => p.Id == request.PlayoutId, cancellationToken);

        if (playout == null)
        {
            return BaseError.New($"Playout with ID {request.PlayoutId} not found.");
        }

        PlayoutScheduleKind scheduleKind = request.SourceKind switch
        {
            ProgramScheduleSourceKind.Schedule => PlayoutScheduleKind.Classic,
            ProgramScheduleSourceKind.Playlist => PlayoutScheduleKind.Sequential,
            ProgramScheduleSourceKind.ExternalJson => PlayoutScheduleKind.ExternalJson,
            _ => PlayoutScheduleKind.Classic
        };

        int? programScheduleId = request.SourceKind == ProgramScheduleSourceKind.Schedule
            ? request.SourceId
            : null;

        playout.ScheduleKind = scheduleKind;
        playout.ProgramScheduleId = programScheduleId;
        playout.SourceKind = request.SourceKind;
        playout.SourceId = request.SourceId;
        playout.ScheduleFile = request.ScheduleFile;
        playout.DeliveryMode = request.DeliveryMode;
        playout.DaysToBuild = request.DaysToBuild > 0 ? request.DaysToBuild : 2;
        playout.ScreenLayoutId = request.ScreenLayoutId;
        playout.CalendarMode = request.CalendarMode;
        playout.IsEnabled = request.IsEnabled;

        // Atualizar regras de calendário
        dbContext.PlayoutCalendarRules.RemoveRange(playout.CalendarRules);
        playout.CalendarRules = request.CalendarRules?.Select(r => new PlayoutCalendarRule
        {
            PlayoutId = playout.Id,
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
        }).ToList() ?? new List<PlayoutCalendarRule>();

        await dbContext.SaveChangesAsync(cancellationToken);

        if (playout.IsEnabled)
        {
            await workerChannel.WriteAsync(new BuildPlayout(playout.Id, PlayoutBuildMode.Reset), cancellationToken);
        }

        await workerChannel.WriteAsync(new RefreshChannelList(), cancellationToken);

        return Unit.Default;
    }
}
