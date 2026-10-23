using System;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Scheduling;
using LanguageExt;

namespace ErsatzTV.Core.Interfaces.Scheduling;

public interface IDirectSourcePlayoutBuilder
{
    Task<Either<BaseError, PlayoutBuildResult>> Build(
        DateTimeOffset start,
        Playout playout,
        PlayoutReferenceData referenceData,
        PlayoutBuildMode mode,
        CancellationToken cancellationToken);
}
