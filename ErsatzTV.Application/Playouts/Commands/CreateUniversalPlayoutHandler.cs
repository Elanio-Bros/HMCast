using System.Threading.Channels;
using ErsatzTV.Application.Channels;
using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Scheduling;
using ErsatzTV.Core.Scheduling;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Channel = ErsatzTV.Core.Domain.Channel;

namespace ErsatzTV.Application.Playouts;

public class CreateUniversalPlayoutHandler(
    ChannelWriter<IBackgroundServiceRequest> workerChannel,
    IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<CreateUniversalPlayout, Either<BaseError, CreatePlayoutResponse>>,
      IRequestHandler<TogglePlayoutEnabled, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, CreatePlayoutResponse>> Handle(
        CreateUniversalPlayout request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        Channel channel = await dbContext.Channels
            .FirstOrDefaultAsync(c => c.Id == request.ChannelId, cancellationToken);

        if (channel == null)
        {
            return BaseError.New($"Channel with ID {request.ChannelId} not found.");
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

        var playout = new Playout
        {
            ChannelId = channel.Id,
            ScheduleKind = scheduleKind,
            ProgramScheduleId = programScheduleId,
            SourceKind = request.SourceKind,
            SourceId = request.SourceId,
            ScheduleFile = request.ScheduleFile,
            DeliveryMode = request.DeliveryMode,
            DaysToBuild = request.DaysToBuild > 0 ? request.DaysToBuild : 2,
            ScreenLayoutId = request.ScreenLayoutId,
            CalendarMode = request.CalendarMode,
            IsEnabled = request.IsEnabled,
            PlayoutMode = channel.PlayoutMode,
            CalendarRules = request.CalendarRules?.Select(r => new PlayoutCalendarRule
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
            }).ToList() ?? new List<PlayoutCalendarRule>()
        };

        await dbContext.Playouts.AddAsync(playout, cancellationToken);
        await dbContext.SaveChangesAsync(cancellationToken);

        if (playout.IsEnabled)
        {
            await workerChannel.WriteAsync(new BuildPlayout(playout.Id, PlayoutBuildMode.Reset), cancellationToken);
        }

        await workerChannel.WriteAsync(new RefreshChannelList(), cancellationToken);

        return new CreatePlayoutResponse(playout.Id);
    }

    public async Task<Either<BaseError, Unit>> Handle(
        TogglePlayoutEnabled request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        Playout playout = await dbContext.Playouts
            .FirstOrDefaultAsync(p => p.Id == request.PlayoutId, cancellationToken);

        if (playout == null)
        {
            return BaseError.New($"Playout with ID {request.PlayoutId} not found.");
        }

        playout.IsEnabled = request.IsEnabled;
        await dbContext.SaveChangesAsync(cancellationToken);

        if (playout.IsEnabled)
        {
            await workerChannel.WriteAsync(new BuildPlayout(playout.Id, PlayoutBuildMode.Refresh), cancellationToken);
        }

        await workerChannel.WriteAsync(new RefreshChannelList(), cancellationToken);

        return Unit.Default;
    }
}
