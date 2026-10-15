using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;
using System;

namespace ErsatzTV.Application.MediaItems;

public record AddMediaSkip(
    int MediaItemId,
    TimeSpan Start,
    TimeSpan End,
    MediaSkipKind Kind,
    MediaSkipSource Source) : IRequest<Either<BaseError, Unit>>;
