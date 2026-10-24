using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaCollections;

public class GetAllPlaylistsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetAllPlaylists, List<PlaylistViewModel>>
{
    public async Task<List<PlaylistViewModel>> Handle(
        GetAllPlaylists request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        return await dbContext.Playlists
            .AsNoTracking()
            .ToListAsync(cancellationToken)
            .Map(items => items.Map(Mapper.ProjectToViewModel).ToList());
    }
}
