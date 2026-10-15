using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;
using System;
using System.Collections.Generic;

namespace ErsatzTV.Application.MediaItems;

public record UpdateMediaSkipItem(TimeSpan Start, TimeSpan End, MediaSkipKind Kind);

public record UpdateMediaSkips(
    int MediaItemId,
    List<UpdateMediaSkipItem> Skips) : IRequest<Either<BaseError, Unit>>;
