using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Interfaces.Repositories;
using ErsatzTV.Core.Interfaces.Streaming;
using LanguageExt;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace ErsatzTV.Core.Streaming;

public class ChannelPreCacheService : IChannelPreCacheService
{
    private readonly IServiceScopeFactory _serviceScopeFactory;
    private readonly ILogger<ChannelPreCacheService> _logger;
    private readonly ConcurrentDictionary<string, PreCachedChannelSession> _sessions = new();

    public ChannelPreCacheService(
        IServiceScopeFactory serviceScopeFactory,
        ILogger<ChannelPreCacheService> logger)
    {
        _serviceScopeFactory = serviceScopeFactory;
        _logger = logger;
    }

    public Option<PreCachedChannelSession> GetPreCachedSession(string channelNumber)
    {
        if (_sessions.TryGetValue(channelNumber, out PreCachedChannelSession session))
        {
            if (DateTimeOffset.UtcNow < session.ItemFinish)
            {
                return session;
            }

            // Sessão expirada, remove do cache
            _sessions.TryRemove(channelNumber, out _);
        }

        return Option<PreCachedChannelSession>.None;
    }

    public async Task WarmupChannel(string channelNumber, CancellationToken cancellationToken)
    {
        try
        {
            using IServiceScope scope = _serviceScopeFactory.CreateScope();
            IChannelRepository channelRepository = scope.ServiceProvider.GetRequiredService<IChannelRepository>();

            Option<Channel> maybeChannel = await channelRepository.GetByNumber(channelNumber);
            if (maybeChannel.IsNone)
            {
                return;
            }

            Channel channel = (Channel)maybeChannel;
            if (channel.IdleBehavior != ChannelIdleBehavior.PreCache)
            {
                return;
            }

            DateTimeOffset now = DateTimeOffset.UtcNow;
            Playout activePlayout = channel.Playouts?.FirstOrDefault(p => p.IsEnabled);
            if (activePlayout is null || activePlayout.Items is null || activePlayout.Items.Count == 0)
            {
                return;
            }

            PlayoutItem currentItem = activePlayout.Items.FirstOrDefault(i => i.Start <= now && i.Finish > now);
            if (currentItem is null)
            {
                return;
            }

            PlayoutItem nextItem = activePlayout.Items.FirstOrDefault(i => i.Start >= currentItem.Finish);
            TimeSpan seek = now - currentItem.Start;

            string mediaPath = currentItem.MediaItem switch
            {
                Episode episode => episode.MediaVersions?.FirstOrDefault()?.MediaFiles?.FirstOrDefault()?.Path ?? string.Empty,
                Movie movie => movie.MediaVersions?.FirstOrDefault()?.MediaFiles?.FirstOrDefault()?.Path ?? string.Empty,
                MusicVideo mv => mv.MediaVersions?.FirstOrDefault()?.MediaFiles?.FirstOrDefault()?.Path ?? string.Empty,
                OtherVideo ov => ov.MediaVersions?.FirstOrDefault()?.MediaFiles?.FirstOrDefault()?.Path ?? string.Empty,
                Song song => song.MediaVersions?.FirstOrDefault()?.MediaFiles?.FirstOrDefault()?.Path ?? string.Empty,
                _ => string.Empty
            };

            var session = new PreCachedChannelSession(
                channel.Number,
                channel.Id,
                currentItem,
                nextItem,
                mediaPath,
                seek,
                now,
                currentItem.Finish);

            _sessions[channelNumber] = session;
            _logger.LogDebug(
                "PreCache warmed up in RAM for channel {ChannelNumber} at seek {Seek} (0% GPU in idle)",
                channelNumber,
                seek);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to warmup PreCache for channel {ChannelNumber}", channelNumber);
        }
    }

    public async Task WarmupAllPreCacheChannels(CancellationToken cancellationToken)
    {
        try
        {
            using IServiceScope scope = _serviceScopeFactory.CreateScope();
            IChannelRepository channelRepository = scope.ServiceProvider.GetRequiredService<IChannelRepository>();

            List<Channel> channels = await channelRepository.GetAll(cancellationToken);
            List<Channel> preCacheChannels = channels
                .Where(c => c.IsEnabled && c.IdleBehavior == ChannelIdleBehavior.PreCache)
                .ToList();

            foreach (Channel channel in preCacheChannels)
            {
                await WarmupChannel(channel.Number, cancellationToken);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to warmup all PreCache channels");
        }
    }

    public void UpdateSeek(string channelNumber, TimeSpan newSeek)
    {
        if (_sessions.TryGetValue(channelNumber, out PreCachedChannelSession session))
        {
            _sessions[channelNumber] = session with { CurrentSeek = newSeek };
        }
    }

    public void Invalidate(string channelNumber)
    {
        _sessions.TryRemove(channelNumber, out _);
    }
}
