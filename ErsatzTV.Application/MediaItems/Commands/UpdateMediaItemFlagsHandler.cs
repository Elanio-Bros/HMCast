using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaItems;

public class UpdateMediaItemFlagsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdateMediaItemFlags, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(UpdateMediaItemFlags request, CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        List<MediaItem> mediaItems = await dbContext.MediaItems
            .Where(mi => request.MediaItemIds.Contains(mi.Id))
            .ToListAsync(cancellationToken);

        foreach (MediaItem mediaItem in mediaItems)
        {
            mediaItem.ShowIntro = request.ShowIntro;
            mediaItem.ShowFinish = request.ShowFinish;
            mediaItem.ShowPreview = request.ShowPreview;
            mediaItem.ShowRecap = request.ShowRecap;
            mediaItem.ShowCut = request.ShowCut;
        }

        await dbContext.SaveChangesAsync(cancellationToken);
        return Unit.Default;
    }
}
