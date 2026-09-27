using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Core.Extensions;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaItems;

public class BulkUpdateMediaSkipsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<BulkUpdateMediaSkips, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(BulkUpdateMediaSkips request, CancellationToken cancellationToken)
    {
        if (request.MediaItemIds == null || request.MediaItemIds.Count == 0)
        {
            return BaseError.New("At least one Media Item ID must be provided.");
        }
        
        if (request.IntroDuration.HasValue && request.IntroDuration.Value < TimeSpan.Zero)
        {
            return BaseError.New("IntroDuration must be greater than or equal to zero.");
        }

        if (request.FinishDuration.HasValue && request.FinishDuration.Value < TimeSpan.Zero)
        {
            return BaseError.New("FinishDuration must be greater than or equal to zero.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        List<MediaItem> mediaItems = await dbContext.MediaItems
            .Include(mi => mi.MediaSkips)
            .Include(mi => (mi as Episode).MediaVersions)
            .Include(mi => (mi as Movie).MediaVersions)
            .Where(mi => request.MediaItemIds.Contains(mi.Id))
            .ToListAsync(cancellationToken);

        foreach (MediaItem mediaItem in mediaItems)
        {
            var duration = mediaItem.GetHeadVersion()?.Duration ?? TimeSpan.Zero;
            if (duration == TimeSpan.Zero) continue; // Skip if we don't know duration

            if (request.IntroDuration.HasValue)
            {
                MediaSkip introSkip = mediaItem.MediaSkips.Find(ms => ms.Kind == MediaSkipKind.Intro);
                if (introSkip != null)
                {
                    if (introSkip.Source != MediaSkipSource.Manual)
                    {
                        introSkip.Start = TimeSpan.Zero;
                        introSkip.End = request.IntroDuration.Value;
                        introSkip.Source = MediaSkipSource.Bulk;
                    }
                }
                else
                {
                    introSkip = new MediaSkip
                    {
                        MediaItemId = mediaItem.Id,
                        Kind = MediaSkipKind.Intro,
                        Start = TimeSpan.Zero,
                        End = request.IntroDuration.Value,
                        Source = MediaSkipSource.Bulk
                    };
                    dbContext.MediaSkips.Add(introSkip);
                    mediaItem.MediaSkips.Add(introSkip);
                }
            }

            if (request.FinishDuration.HasValue)
            {
                MediaSkip outroSkip = mediaItem.MediaSkips.Find(ms => ms.Kind == MediaSkipKind.Finish);
                TimeSpan startOutro = duration - request.FinishDuration.Value;
                if (startOutro < TimeSpan.Zero) startOutro = TimeSpan.Zero;

                if (outroSkip != null)
                {
                    if (outroSkip.Source != MediaSkipSource.Manual)
                    {
                        outroSkip.Start = startOutro;
                        outroSkip.End = duration;
                        outroSkip.Source = MediaSkipSource.Bulk;
                    }
                }
                else
                {
                    outroSkip = new MediaSkip
                    {
                        MediaItemId = mediaItem.Id,
                        Kind = MediaSkipKind.Finish,
                        Start = startOutro,
                        End = duration,
                        Source = MediaSkipSource.Bulk
                    };
                    dbContext.MediaSkips.Add(outroSkip);
                    mediaItem.MediaSkips.Add(outroSkip);
                }
            }
        }

        await dbContext.SaveChangesAsync(cancellationToken);
        return Unit.Default;
    }
}
