using System;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Domain;
using LanguageExt;

namespace ErsatzTV.Core.Interfaces.Streaming;

public interface IChannelFallbackSlateService
{
    Task<Option<MediaItem>> GetFallbackMediaItem(Channel channel, CancellationToken cancellationToken);

    Task<Option<PlayoutItem>> CreateFallbackPlayoutItem(
        Channel channel,
        DateTimeOffset start,
        TimeSpan duration,
        CancellationToken cancellationToken);
}
