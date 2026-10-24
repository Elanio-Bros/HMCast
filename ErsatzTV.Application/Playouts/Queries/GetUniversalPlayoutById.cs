using ErsatzTV.Core;
using MediatR;

namespace ErsatzTV.Application.Playouts;

public record GetUniversalPlayoutById(int PlayoutId) : IRequest<Option<UniversalPlayoutViewModel>>;
