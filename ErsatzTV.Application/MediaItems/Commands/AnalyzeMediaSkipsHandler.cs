using System.Diagnostics;
using System.Globalization;
using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Extensions;
using ErsatzTV.Core.Interfaces.Metadata;
using ErsatzTV.Core.Interfaces.Repositories;
using ErsatzTV.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace ErsatzTV.Application.MediaItems;

public class AnalyzeMediaSkipsHandler : IRequestHandler<AnalyzeMediaSkips, Either<BaseError, Unit>>
{
    private readonly IMediaItemRepository _mediaItemRepository;
    private readonly IMetadataRepository _metadataRepository;
    private readonly IDbContextFactory<TvContext> _dbContextFactory;
    private readonly IConfigElementRepository _configElementRepository;
    private readonly ILocalFileSystem _localFileSystem;
    private readonly ILogger<AnalyzeMediaSkipsHandler> _logger;

    public AnalyzeMediaSkipsHandler(
        IMediaItemRepository mediaItemRepository,
        IMetadataRepository metadataRepository,
        IDbContextFactory<TvContext> dbContextFactory,
        IConfigElementRepository configElementRepository,
        ILocalFileSystem localFileSystem,
        ILogger<AnalyzeMediaSkipsHandler> logger)
    {
        _mediaItemRepository = mediaItemRepository;
        _metadataRepository = metadataRepository;
        _dbContextFactory = dbContextFactory;
        _configElementRepository = configElementRepository;
        _localFileSystem = localFileSystem;
        _logger = logger;
    }

    public async Task<Either<BaseError, Unit>> Handle(AnalyzeMediaSkips request, CancellationToken cancellationToken)
    {
        try
        {
            _logger.LogInformation("Analyzing media skips for item {MediaItemId} using blackdetect", request.MediaItemId);

            await using TvContext dbContext = await _dbContextFactory.CreateDbContextAsync(cancellationToken);
            MediaItem existingMediaItem = await dbContext.MediaItems
                .Include(mi => (mi as Movie).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(mi => (mi as Episode).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .FirstOrDefaultAsync(mi => mi.Id == request.MediaItemId, cancellationToken);

            if (existingMediaItem == null)
            {
                return BaseError.New("Media item not found");
            }

            MediaVersion version = existingMediaItem.GetHeadVersion();
            string path = version?.MediaFiles.HeadOrNone().Match(f => f.Path, () => string.Empty);

            if (string.IsNullOrEmpty(path) || !System.IO.File.Exists(path))
            {
                return BaseError.New("Media file not found");
            }

            Option<string> ffmpegPathOption = await _configElementRepository.GetValue<string>(ConfigElementKey.FFmpegPath, cancellationToken);
            string ffmpegPath = ffmpegPathOption.IfNone("ffmpeg");

            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = ffmpegPath,
                    Arguments = $"-i \"{path}\" -vf blackdetect=d=2:pic_th=0.98 -an -f null -",
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                }
            };

            process.Start();

            var skips = new List<MediaSkip>();
            double currentStart = 0;

            while (!process.StandardError.EndOfStream)
            {
                string line = await process.StandardError.ReadLineAsync(cancellationToken);
                if (line != null && line.Contains("blackdetect"))
                {
                    if (line.Contains("black_start:"))
                    {
                        var parts = line.Split("black_start:");
                        if (parts.Length > 1)
                        {
                            var timeStr = parts[1].Split(" ")[0];
                            if (double.TryParse(timeStr, NumberStyles.Any, CultureInfo.InvariantCulture, out double startTime))
                            {
                                currentStart = startTime;
                            }
                        }
                    }
                    else if (line.Contains("black_end:"))
                    {
                        var parts = line.Split("black_end:");
                        if (parts.Length > 1)
                        {
                            var timeStr = parts[1].Split(" ")[0];
                            if (double.TryParse(timeStr, NumberStyles.Any, CultureInfo.InvariantCulture, out double endTime))
                            {
                                skips.Add(new MediaSkip
                                {
                                    Kind = MediaSkipKind.Cut,
                                    Start = TimeSpan.FromSeconds(currentStart),
                                    End = TimeSpan.FromSeconds(endTime)
                                });
                            }
                        }
                    }
                }
            }

            await process.WaitForExitAsync(cancellationToken);

            if (skips.Count > 0)
            {
                await _metadataRepository.UpdateMediaSkips(existingMediaItem, skips, MediaSkipSource.Blackdetect, cancellationToken);
            }

            return Unit.Default;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error analyzing media skips");
            return BaseError.New(ex.Message);
        }
    }
}
