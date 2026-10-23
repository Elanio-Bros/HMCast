using System;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Scheduling;
using LanguageExt;

namespace ErsatzTV.Core.Interfaces.Scheduling;

public interface IUniversalPlayoutRouter
{
    Task<Either<BaseError, PlayoutBuildResult>> RouteAndBuild(
        DateTimeOffset start,
        Playout playout,
        PlayoutReferenceData referenceData,
        PlayoutBuildMode mode,
        CancellationToken cancellationToken);
}
