using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaCollections;

public class CreatePlaylistHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<CreatePlaylist, Either<BaseError, PlaylistViewModel>>
{
    public async Task<Either<BaseError, PlaylistViewModel>> Handle(
        CreatePlaylist request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);
        Validation<BaseError, Playlist> validation = await Validate(dbContext, request);
        return await validation.Apply(playlist => PersistPlaylist(dbContext, playlist));
    }

    private static async Task<PlaylistViewModel> PersistPlaylist(TvContext dbContext, Playlist playlist)
    {
        await dbContext.Playlists.AddAsync(playlist);
        await dbContext.SaveChangesAsync();
        return Mapper.ProjectToViewModel(playlist);
    }

    private static async Task<Validation<BaseError, Playlist>> Validate(TvContext dbContext, CreatePlaylist request) =>
        (await ValidatePlaylistName(dbContext, request)).Map(name => new Playlist
        {
            Name = name
        });

    private static async Task<Validation<BaseError, string>> ValidatePlaylistName(
        TvContext dbContext,
        CreatePlaylist request)
    {
        if (string.IsNullOrWhiteSpace(request.Name) || request.Name.Length > 50)
        {
            return BaseError.New($"Playlist name \"{request.Name}\" is invalid");
        }

        bool duplicate = await dbContext.Playlists
            .AnyAsync(r => r.Name == request.Name);

        return duplicate
            ? BaseError.New($"A playlist named \"{request.Name}\" already exists")
            : Success<BaseError, string>(request.Name);
    }
}
