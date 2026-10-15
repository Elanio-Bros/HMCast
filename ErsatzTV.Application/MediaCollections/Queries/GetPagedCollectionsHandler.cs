using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using static ErsatzTV.Application.MediaCollections.Mapper;

namespace ErsatzTV.Application.MediaCollections;

public class GetPagedCollectionsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetPagedCollections, PagedMediaCollectionsViewModel>
{
    public async Task<PagedMediaCollectionsViewModel> Handle(
        GetPagedCollections request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);
        int count = await dbContext.Collections.CountAsync(cancellationToken);

        IQueryable<Collection> query = dbContext.Collections.AsNoTracking();

        if (!string.IsNullOrWhiteSpace(request.Query))
        {
            query = query.Where(c => EF.Functions.Like(c.Name, $"%{request.Query}%"));
        }

        var rawPage = await query
            .OrderBy(c => c.Name)
            .Skip(request.PageNum * request.PageSize)
            .Take(request.PageSize)
            .Select(c => new
            {
                c.Id,
                c.Name,
                c.UseCustomPlaybackOrder,
                ItemCount = c.CollectionItems.Count
            })
            .ToListAsync(cancellationToken);

        List<MediaCollectionViewModel> page = rawPage
            .Select(x => new MediaCollectionViewModel(
                CollectionType.Collection,
                x.Id,
                x.Name,
                x.UseCustomPlaybackOrder,
                MediaItemState.Normal,
                x.ItemCount))
            .ToList();

        return new PagedMediaCollectionsViewModel(count, page);
    }
}
