using System;
using ErsatzTV.Core.Domain;

namespace ErsatzTV.Core.Streaming;

public record PreCachedChannelSession(
    string ChannelNumber,
    int ChannelId,
    PlayoutItem CurrentItem,
    PlayoutItem NextItem,
    string MediaFilePath,
    TimeSpan CurrentSeek,
    DateTimeOffset PreparedAt,
    DateTimeOffset ItemFinish);
