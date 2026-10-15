using ErsatzTV.Core;
using ErsatzTV.Core.Errors;
using LanguageExt;
using MediatR;
using System.Collections.Generic;

namespace ErsatzTV.Application.MediaItems;

public record RemoveMediaSkips(List<int> MediaSkipIds) : IRequest<Either<BaseError, Unit>>;
