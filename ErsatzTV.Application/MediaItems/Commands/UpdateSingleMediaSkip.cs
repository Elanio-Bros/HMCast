using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;
using System;

namespace ErsatzTV.Application.MediaItems;

public record UpdateSingleMediaSkip(
    int MediaSkipId,
    TimeSpan Start,
    TimeSpan End,
    MediaSkipKind Kind) : IRequest<Either<BaseError, Unit>>;
