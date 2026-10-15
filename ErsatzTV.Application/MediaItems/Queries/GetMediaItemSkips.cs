using ErsatzTV.Core.Domain;
using MediatR;
using System.Collections.Generic;

namespace ErsatzTV.Application.MediaItems;

public record GetMediaItemSkips(int MediaItemId) : IRequest<List<MediaSkip>>;
