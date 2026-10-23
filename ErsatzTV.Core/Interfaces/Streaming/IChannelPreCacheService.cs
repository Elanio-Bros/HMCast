using System;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core.Streaming;
using LanguageExt;

namespace ErsatzTV.Core.Interfaces.Streaming;

public interface IChannelPreCacheService
{
    Option<PreCachedChannelSession> GetPreCachedSession(string channelNumber);
    Task WarmupChannel(string channelNumber, CancellationToken cancellationToken);
    Task WarmupAllPreCacheChannels(CancellationToken cancellationToken);
    void UpdateSeek(string channelNumber, TimeSpan newSeek);
    void Invalidate(string channelNumber);
}
