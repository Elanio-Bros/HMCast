using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;
using System;
using System.Collections.Generic;

namespace ErsatzTV.Application.MediaItems;

public record CopyMediaSkipsToItems(
    int SourceMediaItemId,
    List<int> SelectedSkipIds,
    List<int> TargetMediaItemIds) : IRequest<Either<BaseError, Unit>>;
