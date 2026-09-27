using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaItems;

public class UpdateMediaSkipsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdateMediaSkips, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(UpdateMediaSkips request, CancellationToken cancellationToken)
    {
        if (request.MediaItemIds == null || request.MediaItemIds.Count == 0)
        {
            return BaseError.New("At least one Media Item ID must be provided.");
        }

        if (request.IntroStart.HasValue && request.IntroEnd.HasValue && request.IntroEnd.Value <= request.IntroStart.Value)
        {
            return BaseError.New("IntroEnd must be greater than IntroStart.");
        }

        if (request.OutroStart.HasValue && request.OutroEnd.HasValue && request.OutroEnd.Value <= request.OutroStart.Value)
        {
            return BaseError.New("OutroEnd must be greater than OutroStart.");
        }

        if (request.IntroEnd.HasValue && request.OutroStart.HasValue && request.OutroStart.Value <= request.IntroEnd.Value)
        {
            return BaseError.New("OutroStart must be greater than IntroEnd.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        List<MediaItem> mediaItems = await dbContext.MediaItems
            .Include(mi => mi.MediaSkips)
            .Where(mi => request.MediaItemIds.Contains(mi.Id))
            .ToListAsync(cancellationToken);

        foreach (MediaItem mediaItem in mediaItems)
        {
            if (request.IntroStart.HasValue && request.IntroEnd.HasValue)
            {
                MediaSkip introSkip = mediaItem.MediaSkips.Find(ms => ms.Kind == MediaSkipKind.Intro);
                if (introSkip != null)
                {
                    introSkip.Start = request.IntroStart.Value;
                    introSkip.End = request.IntroEnd.Value;
                    introSkip.Source = MediaSkipSource.Manual;
                }
                else
                {
                    introSkip = new MediaSkip
                    {
                        MediaItemId = mediaItem.Id,
                        Kind = MediaSkipKind.Intro,
                        Start = request.IntroStart.Value,
                        End = request.IntroEnd.Value,
                        Source = MediaSkipSource.Manual
                    };
                    dbContext.MediaSkips.Add(introSkip);
                    mediaItem.MediaSkips.Add(introSkip);
                }
            }

            if (request.OutroStart.HasValue && request.OutroEnd.HasValue)
            {
                MediaSkip outroSkip = mediaItem.MediaSkips.Find(ms => ms.Kind == MediaSkipKind.Finish);
                if (outroSkip != null)
                {
                    outroSkip.Start = request.OutroStart.Value;
                    outroSkip.End = request.OutroEnd.Value;
                    outroSkip.Source = MediaSkipSource.Manual;
                }
                else
                {
                    outroSkip = new MediaSkip
                    {
                        MediaItemId = mediaItem.Id,
                        Kind = MediaSkipKind.Finish,
                        Start = request.OutroStart.Value,
                        End = request.OutroEnd.Value,
                        Source = MediaSkipSource.Manual
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
