using ErsatzTV.Core;

namespace ErsatzTV.Application.MediaCollections;

public record CreatePlaylist(string Name) : IRequest<Either<BaseError, PlaylistViewModel>>;
