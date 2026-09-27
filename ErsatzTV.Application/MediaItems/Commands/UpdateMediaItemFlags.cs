using ErsatzTV.Core;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;

namespace ErsatzTV.Application.MediaItems;

public record UpdateMediaItemFlags(
    List<int> MediaItemIds,
    bool ShowIntro,
    bool ShowFinish,
    bool ShowPreview,
    bool ShowRecap,
    bool ShowCut) : IRequest<Either<BaseError, Unit>>;
