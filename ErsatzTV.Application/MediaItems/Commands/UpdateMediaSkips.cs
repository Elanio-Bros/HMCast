using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;

namespace ErsatzTV.Application.MediaItems;

public record UpdateMediaSkips(
    List<int> MediaItemIds,
    TimeSpan? IntroStart,
    TimeSpan? IntroEnd,
    TimeSpan? OutroStart,
    TimeSpan? OutroEnd) : IRequest<Either<BaseError, Unit>>;
