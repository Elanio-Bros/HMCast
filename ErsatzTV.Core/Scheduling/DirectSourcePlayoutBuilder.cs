using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Extensions;
using ErsatzTV.Core.Interfaces.Repositories;
using ErsatzTV.Core.Interfaces.Scheduling;
using LanguageExt;
using Microsoft.Extensions.Logging;

namespace ErsatzTV.Core.Scheduling;

public class DirectSourcePlayoutBuilder : IDirectSourcePlayoutBuilder
{
    private readonly IMediaCollectionRepository _mediaCollectionRepository;
    private readonly ILogger<DirectSourcePlayoutBuilder> _logger;

    public DirectSourcePlayoutBuilder(
        IMediaCollectionRepository mediaCollectionRepository,
        ILogger<DirectSourcePlayoutBuilder> logger)
    {
        _mediaCollectionRepository = mediaCollectionRepository;
        _logger = logger;
    }

    public async Task<Either<BaseError, PlayoutBuildResult>> Build(
        DateTimeOffset start,
        Playout playout,
        PlayoutReferenceData referenceData,
        PlayoutBuildMode mode,
        CancellationToken cancellationToken)
    {
        if (!playout.SourceId.HasValue)
        {
            _logger.LogWarning("Playout {PlayoutId} has no SourceId configured for direct playback", playout.Id);
            return PlayoutBuildResult.Empty;
        }

        List<MediaItem> mediaItems = playout.SourceKind switch
        {
            ProgramScheduleSourceKind.Collection => await _mediaCollectionRepository.GetItems(playout.SourceId.Value),
            ProgramScheduleSourceKind.MediaItem => await LoadSingleMediaItem(playout.SourceId.Value),
            _ => await _mediaCollectionRepository.GetItems(playout.SourceId.Value)
        };

        if (mediaItems.Count == 0)
        {
            _logger.LogWarning("Playout {PlayoutId} found 0 items in source {SourceId}", playout.Id, playout.SourceId);
            return PlayoutBuildResult.Empty;
        }

        // Aplicar regras dos 4 modos de PlayoutDeliveryMode (HMCast 3.0)
        int itemIndex = 0;

        switch (playout.DeliveryMode)
        {
            case PlayoutDeliveryMode.Shuffle:
                var random = new Random(playout.Seed);
                mediaItems = mediaItems.OrderBy(_ => random.Next()).ToList();
                break;

            case PlayoutDeliveryMode.Conseguinte:
                // Retoma a reprodução sequencial a partir do último item tocado
                if (referenceData?.ExistingItems?.Count > 0)
                {
                    int? lastMediaId = referenceData.ExistingItems
                        .OrderBy(i => i.Finish)
                        .LastOrDefault()?.MediaItemId;

                    if (lastMediaId.HasValue)
                    {
                        int found = mediaItems.FindIndex(m => m.Id == lastMediaId.Value);
                        if (found >= 0)
                        {
                            itemIndex = (found + 1) % mediaItems.Count;
                        }
                    }
                }
                break;

            case PlayoutDeliveryMode.PlayOnce:
            case PlayoutDeliveryMode.Loop:
            default:
                // Modo sequencial / loop padrão iniciando do índice 0
                break;
        }

        DateTimeOffset current = start;
        DateTimeOffset targetEnd = start.AddDays(Math.Max(1, playout.DaysToBuild));
        var itemsToAdd = new List<PlayoutItem>();

        while (current < targetEnd && !cancellationToken.IsCancellationRequested)
        {
            MediaItem mediaItem = mediaItems[itemIndex % mediaItems.Count];
            TimeSpan duration = GetMediaDuration(mediaItem);

            if (duration <= TimeSpan.Zero)
            {
                duration = TimeSpan.FromMinutes(30); // fallback padrão
            }

            DateTimeOffset itemFinish = current.Add(duration);

            var playoutItem = new PlayoutItem
            {
                PlayoutId = playout.Id,
                MediaItemId = mediaItem.Id,
                Start = current.UtcDateTime,
                Finish = itemFinish.UtcDateTime,
                FillerKind = FillerKind.None
            };

            itemsToAdd.Add(playoutItem);
            current = itemFinish;
            itemIndex++;

            if (playout.DeliveryMode == PlayoutDeliveryMode.PlayOnce && itemIndex >= mediaItems.Count)
            {
                break;
            }
        }

        _logger.LogInformation(
            "Built {Count} timeline items for direct playout {PlayoutId} ({DeliveryMode})",
            itemsToAdd.Count,
            playout.Id,
            playout.DeliveryMode);

        return PlayoutBuildResult.Empty with
        {
            AddedItems = itemsToAdd,
            RemoveBefore = start,
            ClearItems = mode is PlayoutBuildMode.Reset
        };
    }

    private async Task<List<MediaItem>> LoadSingleMediaItem(int mediaItemId)
    {
        List<Movie> movies = await _mediaCollectionRepository.GetMovie(mediaItemId);
        if (movies.Count > 0) return movies.Cast<MediaItem>().ToList();

        List<Episode> episodes = await _mediaCollectionRepository.GetEpisode(mediaItemId);
        if (episodes.Count > 0) return episodes.Cast<MediaItem>().ToList();

        List<MusicVideo> musicVideos = await _mediaCollectionRepository.GetMusicVideo(mediaItemId);
        if (musicVideos.Count > 0) return musicVideos.Cast<MediaItem>().ToList();

        List<OtherVideo> otherVideos = await _mediaCollectionRepository.GetOtherVideo(mediaItemId);
        if (otherVideos.Count > 0) return otherVideos.Cast<MediaItem>().ToList();

        List<Song> songs = await _mediaCollectionRepository.GetSong(mediaItemId);
        if (songs.Count > 0) return songs.Cast<MediaItem>().ToList();

        return new List<MediaItem>();
    }

    private static TimeSpan GetMediaDuration(MediaItem mediaItem)
    {
        return mediaItem switch
        {
            Movie m => m.MediaVersions?.FirstOrDefault()?.Duration ?? TimeSpan.Zero,
            Episode e => e.MediaVersions?.FirstOrDefault()?.Duration ?? TimeSpan.Zero,
            MusicVideo mv => mv.MediaVersions?.FirstOrDefault()?.Duration ?? TimeSpan.Zero,
            OtherVideo ov => ov.MediaVersions?.FirstOrDefault()?.Duration ?? TimeSpan.Zero,
            Song s => s.MediaVersions?.FirstOrDefault()?.Duration ?? TimeSpan.Zero,
            _ => TimeSpan.Zero
        };
    }
}
