using System.Globalization;
using ErsatzTV.Application.Artworks;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.Channels.Queries;

public class GetBroadcastDashboardHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetBroadcastDashboard, BroadcastDashboardModel>
{
    public async Task<BroadcastDashboardModel> Handle(
        GetBroadcastDashboard request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        int totalChannels = await dbContext.Channels.CountAsync(cancellationToken);
        int activeChannels = await dbContext.Channels.CountAsync(c => c.IsEnabled, cancellationToken);
        int activePlayouts = await dbContext.Playouts.CountAsync(p => p.IsEnabled, cancellationToken);
        int preCacheChannels = await dbContext.Channels.CountAsync(c => c.IsEnabled && c.PreCache > 0, cancellationToken);

        List<TimeSpan> libraryDurations = await dbContext.MediaVersions
            .AsNoTracking()
            .Select(mv => mv.Duration)
            .ToListAsync(cancellationToken);
        double totalLibraryHours = Math.Round(libraryDurations.Sum(d => d.TotalHours), 1);

        List<Channel> channels = await dbContext.Channels
            .AsNoTracking()
            .Include(c => c.Artwork)
            .Include(c => c.Playouts)
            .OrderBy(c => c.SortNumber)
            .ToListAsync(cancellationToken);

        DateTime utcNow = DateTime.UtcNow;
        var channelItems = new List<BroadcastDashboardChannelItem>();

        foreach (Channel channel in channels)
        {
            ArtworkContentTypeModel logo = Mapper.ProjectToViewModel(channel, channel.Playouts.Count).Logo;
            List<int> playoutIds = channel.Playouts.Select(p => p.Id).ToList();

            PlayoutItem currentItem = null;
            PlayoutItem nextItem = null;

            if (playoutIds.Count > 0)
            {
                currentItem = await dbContext.PlayoutItems
                    .AsNoTracking()
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Movie).MovieMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Episode).EpisodeMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Episode).Season.Show.ShowMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as MusicVideo).MusicVideoMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Song).SongMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as OtherVideo).OtherVideoMetadata)
                    .Where(i => playoutIds.Contains(i.PlayoutId) && i.Start <= utcNow && i.Finish > utcNow)
                    .OrderByDescending(i => i.Start)
                    .FirstOrDefaultAsync(cancellationToken);

                nextItem = await dbContext.PlayoutItems
                    .AsNoTracking()
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Movie).MovieMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Episode).EpisodeMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Episode).Season.Show.ShowMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as MusicVideo).MusicVideoMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as Song).SongMetadata)
                    .Include(i => i.MediaItem)
                        .ThenInclude(mi => (mi as OtherVideo).OtherVideoMetadata)
                    .Where(i => playoutIds.Contains(i.PlayoutId) && i.Start > utcNow)
                    .OrderBy(i => i.Start)
                    .FirstOrDefaultAsync(cancellationToken);
            }

            bool isOnAir = channel.IsEnabled && currentItem != null;
            string currentItemTitle = currentItem != null
                ? Playouts.Mapper.GetDisplayTitle(currentItem.MediaItem, currentItem.ChapterTitle)
                : string.Empty;

            string nextItemTitle = nextItem != null
                ? Playouts.Mapper.GetDisplayTitle(nextItem.MediaItem, nextItem.ChapterTitle)
                : string.Empty;

            double progressPercentage = 0.0;
            if (currentItem != null)
            {
                double totalSec = (currentItem.Finish - currentItem.Start).TotalSeconds;
                if (totalSec > 0)
                {
                    double elapsedSec = (utcNow - currentItem.Start).TotalSeconds;
                    progressPercentage = Math.Clamp(Math.Round((elapsedSec / totalSec) * 100.0, 1), 0.0, 100.0);
                }
            }

            channelItems.Add(new BroadcastDashboardChannelItem(
                channel.Id,
                channel.Number,
                channel.Name,
                logo,
                channel.Mode,
                channel.PreCache,
                channel.IsEnabled,
                isOnAir,
                currentItemTitle,
                nextItemTitle,
                progressPercentage,
                currentItem?.StartOffset,
                currentItem?.FinishOffset
            ));
        }

        return new BroadcastDashboardModel(
            activeChannels,
            totalChannels,
            activePlayouts,
            preCacheChannels,
            totalLibraryHours,
            channelItems
        );
    }
}
