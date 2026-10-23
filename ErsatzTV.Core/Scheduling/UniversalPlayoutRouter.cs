using System;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Interfaces.Scheduling;
using LanguageExt;
using Microsoft.Extensions.Logging;

namespace ErsatzTV.Core.Scheduling;

public class UniversalPlayoutRouter : IUniversalPlayoutRouter
{
    private readonly IPlayoutBuilder _playoutBuilder;
    private readonly ISequentialPlayoutBuilder _sequentialPlayoutBuilder;
    private readonly IDirectSourcePlayoutBuilder _directSourcePlayoutBuilder;
    private readonly ILogger<UniversalPlayoutRouter> _logger;

    public UniversalPlayoutRouter(
        IPlayoutBuilder playoutBuilder,
        ISequentialPlayoutBuilder sequentialPlayoutBuilder,
        IDirectSourcePlayoutBuilder directSourcePlayoutBuilder,
        ILogger<UniversalPlayoutRouter> logger)
    {
        _playoutBuilder = playoutBuilder;
        _sequentialPlayoutBuilder = sequentialPlayoutBuilder;
        _directSourcePlayoutBuilder = directSourcePlayoutBuilder;
        _logger = logger;
    }

    public async Task<Either<BaseError, PlayoutBuildResult>> RouteAndBuild(
        DateTimeOffset start,
        Playout playout,
        PlayoutReferenceData referenceData,
        PlayoutBuildMode mode,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Routing playout {PlayoutId} build with SourceKind {SourceKind}",
            playout.Id,
            playout.SourceKind);

        return playout.SourceKind switch
        {
            ProgramScheduleSourceKind.Schedule => await _playoutBuilder.Build(start, playout, referenceData, mode, cancellationToken),
            ProgramScheduleSourceKind.Playlist => await _sequentialPlayoutBuilder.Build(start, playout, referenceData, mode, cancellationToken),
            _ => await _directSourcePlayoutBuilder.Build(start, playout, referenceData, mode, cancellationToken)
        };
    }
}
