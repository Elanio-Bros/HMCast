using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace ErsatzTV.Application.MediaItems;

public class UpdateMediaSkipsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdateMediaSkips, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(UpdateMediaSkips request, CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        MediaItem mediaItem = await dbContext.MediaItems
            .Include(mi => mi.MediaSkips)
            .FirstOrDefaultAsync(mi => mi.Id == request.MediaItemId, cancellationToken);

        if (mediaItem == null)
        {
            return BaseError.New($"MediaItem with ID {request.MediaItemId} was not found.");
        }

        // Remove existing manual skips for this item
        var existingManualSkips = mediaItem.MediaSkips.Where(s => s.Source == MediaSkipSource.Manual).ToList();
        foreach (var skip in existingManualSkips)
        {
            dbContext.MediaSkips.Remove(skip);
            mediaItem.MediaSkips.Remove(skip);
        }

        // Add new skips
        if (request.Skips != null)
        {
            foreach (var item in request.Skips)
            {
                if (item.End > item.Start)
                {
                    var newSkip = new MediaSkip
                    {
                        MediaItemId = request.MediaItemId,
                        Start = item.Start,
                        End = item.End,
                        Kind = item.Kind,
                        Source = MediaSkipSource.Manual
                    };
                    dbContext.MediaSkips.Add(newSkip);
                    mediaItem.MediaSkips.Add(newSkip);
                }
            }
        }

        await dbContext.SaveChangesAsync(cancellationToken);
        return Unit.Default;
    }
}
