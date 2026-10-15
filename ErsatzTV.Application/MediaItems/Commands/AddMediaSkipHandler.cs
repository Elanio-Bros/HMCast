using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;
using System.Threading;
using System.Threading.Tasks;

namespace ErsatzTV.Application.MediaItems;

public class AddMediaSkipHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<AddMediaSkip, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(AddMediaSkip request, CancellationToken cancellationToken)
    {
        if (request.End <= request.Start)
        {
            return BaseError.New("End time must be greater than start time.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        MediaItem mediaItem = await dbContext.MediaItems
            .Include(mi => mi.MediaSkips)
            .FirstOrDefaultAsync(mi => mi.Id == request.MediaItemId, cancellationToken);

        if (mediaItem == null)
        {
            return BaseError.New($"MediaItem {request.MediaItemId} does not exist.");
        }

        var skip = new MediaSkip
        {
            MediaItemId = request.MediaItemId,
            Start = request.Start,
            End = request.End,
            Kind = request.Kind,
            Source = request.Source
        };

        dbContext.MediaSkips.Add(skip);
        mediaItem.MediaSkips.Add(skip);

        await dbContext.SaveChangesAsync(cancellationToken);

        return Unit.Default;
    }
}
