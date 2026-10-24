using MediatR;

namespace ErsatzTV.Application.MediaCollections;

public record GetAllPlaylists : IRequest<List<PlaylistViewModel>>;
