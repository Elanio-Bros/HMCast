using ErsatzTV.Core;

namespace ErsatzTV.Application.MediaCollections;

public record UpdatePlaylist(int PlaylistId, int PlaylistGroupId, string Name)
    : IRequest<Either<BaseError, PlaylistViewModel>>;
