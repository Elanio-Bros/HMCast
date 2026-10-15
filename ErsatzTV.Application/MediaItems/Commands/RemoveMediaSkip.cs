using ErsatzTV.Core;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;

namespace ErsatzTV.Application.MediaItems;

public record RemoveMediaSkip(int MediaSkipId) : IRequest<Either<BaseError, Unit>>;
