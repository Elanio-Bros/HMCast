using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Interfaces.Repositories;
using ErsatzTV.Core.Interfaces.Streaming;
using LanguageExt;
using Microsoft.Extensions.Logging;

namespace ErsatzTV.Core.Streaming;

public class ChannelFallbackSlateService : IChannelFallbackSlateService
{
    private readonly IMediaCollectionRepository _mediaCollectionRepository;
    private readonly ILogger<ChannelFallbackSlateService> _logger;

    public ChannelFallbackSlateService(
        IMediaCollectionRepository mediaCollectionRepository,
        ILogger<ChannelFallbackSlateService> logger)
    {
        _mediaCollectionRepository = mediaCollectionRepository;
        _logger = logger;
    }

    public async Task<Option<MediaItem>> GetFallbackMediaItem(Channel channel, CancellationToken cancellationToken)
    {
        if (channel?.FallbackSlate == null || channel.FallbackSlate.Mode == FallbackSlateMode.Disabled)
        {
            return Option<MediaItem>.None;
        }

        ChannelFallbackSlate slate = channel.FallbackSlate;

        switch (slate.Mode)
        {
            case FallbackSlateMode.SingleMedia:
                if (slate.MediaItemId.HasValue)
                {
                    List<MediaItem> single = await LoadSingleMediaItem(slate.MediaItemId.Value);
                    if (single.Count > 0)
                    {
                        return Option<MediaItem>.Some(single[0]);
                    }
                }
                break;

            case FallbackSlateMode.Collection:
                if (slate.CollectionId.HasValue)
                {
                    List<MediaItem> items = await _mediaCollectionRepository.GetItems(slate.CollectionId.Value);
                    if (items.Count > 0)
                    {
                        return Option<MediaItem>.Some(items[0]);
                    }
                }
                break;

            case FallbackSlateMode.Playlist:
                if (slate.PlaylistId.HasValue)
                {
                    List<MediaItem> items = await _mediaCollectionRepository.GetPlaylistItems(slate.PlaylistId.Value, cancellationToken);
                    if (items.Count > 0)
                    {
                        return Option<MediaItem>.Some(items[0]);
                    }
                }
                break;
        }

        _logger.LogWarning("Fallback slate for channel {ChannelNumber} could not resolve any media item", channel.Number);
        return Option<MediaItem>.None;
    }

    public async Task<Option<PlayoutItem>> CreateFallbackPlayoutItem(
        Channel channel,
        DateTimeOffset start,
        TimeSpan duration,
        CancellationToken cancellationToken)
    {
        Option<MediaItem> maybeMedia = await GetFallbackMediaItem(channel, cancellationToken);
        foreach (MediaItem media in maybeMedia)
        {
            var playoutItem = new PlayoutItem
            {
                MediaItemId = media.Id,
                Start = start.UtcDateTime,
                Finish = start.Add(duration).UtcDateTime,
                FillerKind = FillerKind.Fallback,
                CustomTitle = channel.FallbackSlate?.CustomTitle
            };

            return Option<PlayoutItem>.Some(playoutItem);
        }

        return Option<PlayoutItem>.None;
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

        List<Image> images = await _mediaCollectionRepository.GetImage(mediaItemId);
        if (images.Count > 0) return images.Cast<MediaItem>().ToList();

        List<RemoteStream> remoteStreams = await _mediaCollectionRepository.GetRemoteStream(mediaItemId);
        if (remoteStreams.Count > 0) return remoteStreams.Cast<MediaItem>().ToList();

        return new List<MediaItem>();
    }
}
