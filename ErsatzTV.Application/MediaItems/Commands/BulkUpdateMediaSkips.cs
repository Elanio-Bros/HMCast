using ErsatzTV.Core;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;

namespace ErsatzTV.Application.MediaItems;

public record BulkUpdateMediaSkips(
    List<int> MediaItemIds,
    TimeSpan? IntroDuration,
    TimeSpan? FinishDuration) : IRequest<Either<BaseError, Unit>>;
