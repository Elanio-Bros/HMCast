using ErsatzTV.Application.Artworks;
using ErsatzTV.Core.Domain;
using MediatR;

namespace ErsatzTV.Application.Channels.Queries;

public record BroadcastDashboardChannelItem(
    int ChannelId,
    string Number,
    string Name,
    ArtworkContentTypeModel Logo,
    ChannelMode Mode,
    int PreCache,
    bool IsEnabled,
    bool IsOnAir,
    string CurrentItemTitle,
    string NextItemTitle,
    double ProgressPercentage,
    DateTimeOffset? CurrentItemStart,
    DateTimeOffset? CurrentItemFinish
);

public record BroadcastDashboardModel(
    int ActiveChannelsCount,
    int TotalChannelsCount,
    int ActivePlayoutsCount,
    int PreCacheChannelsCount,
    double TotalLibraryHours,
    List<BroadcastDashboardChannelItem> Channels
);

public record GetBroadcastDashboard : IRequest<BroadcastDashboardModel>;
