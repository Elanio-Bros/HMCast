using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaCollections;

public class UpdatePlaylistHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdatePlaylist, Either<BaseError, PlaylistViewModel>>
{
    public async Task<Either<BaseError, PlaylistViewModel>> Handle(
        UpdatePlaylist request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);
        Validation<BaseError, Playlist> validation = await Validate(dbContext, request);
        return await validation.Apply(playlist => PersistPlaylist(dbContext, playlist));
    }

    private static async Task<PlaylistViewModel> PersistPlaylist(TvContext dbContext, Playlist playlist)
    {
        await dbContext.SaveChangesAsync();
        return Mapper.ProjectToViewModel(playlist);
    }

    private static async Task<Validation<BaseError, Playlist>> Validate(TvContext dbContext, UpdatePlaylist request)
    {
        Playlist playlist = await dbContext.Playlists
            .FirstOrDefaultAsync(p => p.Id == request.PlaylistId);

        if (playlist == null)
        {
            return BaseError.New($"Playlist with ID {request.PlaylistId} not found");
        }

        if (playlist.IsSystem)
        {
            return BaseError.New("System playlists cannot be modified");
        }

        if (string.IsNullOrWhiteSpace(request.Name) || request.Name.Length > 50)
        {
            return BaseError.New($"Playlist name \"{request.Name}\" is invalid");
        }

        bool duplicate = await dbContext.Playlists
            .AnyAsync(r => r.Id != request.PlaylistId && r.Name == request.Name);

        if (duplicate)
        {
            return BaseError.New($"A playlist named \"{request.Name}\" already exists");
        }

        playlist.Name = request.Name.Trim();

        return playlist;
    }
}
