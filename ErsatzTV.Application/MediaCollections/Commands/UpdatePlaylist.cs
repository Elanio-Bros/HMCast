using ErsatzTV.Core;

namespace ErsatzTV.Application.MediaCollections;

public record UpdatePlaylist(int PlaylistId, string Name) : IRequest<Either<BaseError, PlaylistViewModel>>;
