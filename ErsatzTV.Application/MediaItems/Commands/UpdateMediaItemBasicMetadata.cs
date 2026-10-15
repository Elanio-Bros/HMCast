using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;

namespace ErsatzTV.Application.MediaItems;

public record UpdateMediaItemBasicMetadata(
    int MediaItemId,
    string Title,
    string SortTitle,
    string OriginalTitle,
    int? Year,
    string ContentRating,
    string Plot) : IRequest<Either<BaseError, Unit>>;
