using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Core.Extensions;
using ErsatzTV.Infrastructure.Data;
using ErsatzTV.Infrastructure.Extensions;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaItems;

public class GetMediaItemInfoHandler : IRequestHandler<GetMediaItemInfo, Either<BaseError, MediaItemInfo>>
{
    private readonly IDbContextFactory<TvContext> _dbContextFactory;

    public GetMediaItemInfoHandler(IDbContextFactory<TvContext> dbContextFactory) =>
        _dbContextFactory = dbContextFactory;

    public async Task<Either<BaseError, MediaItemInfo>> Handle(
        GetMediaItemInfo request,
        CancellationToken cancellationToken)
    {
        try
        {
            await using TvContext dbContext = await _dbContextFactory.CreateDbContextAsync(cancellationToken);

            Option<MediaItemInfo> mediaItem = await dbContext.MediaItems
                .AsNoTracking()
                .AsSplitQuery()
                .Include(i => i.LibraryPath)
                .ThenInclude(lp => lp.Library)
                .ThenInclude(l => l.MediaSource)
                // TODO: support all media types here
                .Include(i => (i as Movie).MovieMetadata)
                .ThenInclude(mm => mm.Subtitles)
                .Include(i => (i as Movie).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(i => (i as Movie).MediaVersions)
                .ThenInclude(mv => mv.Chapters)
                .Include(i => (i as Movie).MediaVersions)
                .ThenInclude(mv => mv.Streams)
                .Include(i => (i as Episode).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(i => (i as Episode).MediaVersions)
                .ThenInclude(mv => mv.Chapters)
                .Include(i => (i as Episode).MediaVersions)
                .ThenInclude(mv => mv.Streams)
                .Include(i => (i as Episode).EpisodeMetadata)
                .ThenInclude(em => em.Subtitles)
                .Include(i => (i as Episode).Season)
                .ThenInclude(s => s.Show)
                .ThenInclude(s => s.ShowMetadata)
                .Include(i => (i as OtherVideo).OtherVideoMetadata)
                .ThenInclude(ovm => ovm.Subtitles)
                .Include(i => (i as OtherVideo).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(i => (i as OtherVideo).MediaVersions)
                .ThenInclude(mv => mv.Chapters)
                .Include(i => (i as OtherVideo).MediaVersions)
                .ThenInclude(mv => mv.Streams)
                .Include(i => (i as Image).ImageMetadata)
                .ThenInclude(im => im.Subtitles)
                .Include(i => (i as Image).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(i => (i as Image).MediaVersions)
                .ThenInclude(mv => mv.Chapters)
                .Include(i => (i as Image).MediaVersions)
                .ThenInclude(mv => mv.Streams)
                .Include(i => (i as RemoteStream).RemoteStreamMetadata)
                .ThenInclude(rsm => rsm.Subtitles)
                .Include(i => (i as RemoteStream).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(i => (i as RemoteStream).MediaVersions)
                .ThenInclude(mv => mv.Chapters)
                .Include(i => (i as RemoteStream).MediaVersions)
                .ThenInclude(mv => mv.Streams)
                .Include(i => (i as Song).SongMetadata)
                .ThenInclude(sm => sm.Subtitles)
                .Include(i => (i as Song).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(i => (i as Song).MediaVersions)
                .ThenInclude(mv => mv.Chapters)
                .Include(i => (i as Song).MediaVersions)
                .ThenInclude(mv => mv.Streams)
                .Include(i => (i as MusicVideo).MusicVideoMetadata)
                .ThenInclude(mvm => mvm.Subtitles)
                .Include(i => (i as MusicVideo).MediaVersions)
                .ThenInclude(mv => mv.MediaFiles)
                .Include(i => (i as MusicVideo).MediaVersions)
                .ThenInclude(mv => mv.Chapters)
                .Include(i => (i as MusicVideo).MediaVersions)
                .ThenInclude(mv => mv.Streams)
                .Include(i => (i as MusicVideo).Artist)
                .ThenInclude(a => a.ArtistMetadata)
                .SelectOneAsync(i => i.Id, i => i.Id == request.Id, cancellationToken)
                .MapT(Project);

            return mediaItem.ToEither<BaseError>(new UnableToLocateMediaItem());
        }
        catch (Exception ex)
        {
            return BaseError.New(ex.ToString());
        }
    }

    private static MediaItemInfo Project(MediaItem mediaItem)
    {
        string displayTitle = Playouts.Mapper.GetDisplayTitle(mediaItem, Option<string>.None);

        MediaVersion version = mediaItem.GetHeadVersion();

        string serverName = mediaItem.LibraryPath.Library.MediaSource switch
        {
            PlexMediaSource plexMediaSource => plexMediaSource.ServerName,
            EmbyMediaSource embyMediaSource => embyMediaSource.ServerName,
            JellyfinMediaSource jellyfinMediaSource => jellyfinMediaSource.ServerName,
            _ => null
        };

        var allStreams = version.Streams.OrderBy(s => s.Index).Map(Project).ToList();

        List<Subtitle> subtitles = mediaItem switch
        {
            Movie m => m.MovieMetadata.Map(mm => mm.Subtitles).Flatten().ToList(),
            Episode e => e.EpisodeMetadata.Map(em => em.Subtitles).Flatten().ToList(),
            MusicVideo mv => mv.MusicVideoMetadata.Map(mvm => mvm.Subtitles).Flatten().ToList(),
            Song s => s.SongMetadata.Map(sm => sm.Subtitles).Flatten().ToList(),
            _ => []
        };

        // include external subtitles from local libraries
        if (mediaItem.LibraryPath.Library is LocalLibrary)
        {
            allStreams.AddRange(subtitles.Filter(s => s.SubtitleKind is SubtitleKind.Sidecar).Map(ProjectToStream));
        }

        // set extracted status and file name on each subtitle stream
        foreach (MediaItemInfoStream subtitleStream in allStreams.Filter(s => s.Kind is MediaStreamKind.Subtitle))
        {
            foreach (Subtitle subtitle in subtitles.Filter(s => s.StreamIndex == subtitleStream.Index).HeadOrNone())
            {
                if (!subtitle.IsImage)
                {
                    subtitleStream.IsExtracted = subtitle.IsExtracted;
                }

                subtitleStream.FileName = string.IsNullOrWhiteSpace(subtitle.Path) ? null : subtitle.Path;
            }
        }

        var allChapters = (version.Chapters ?? []).OrderBy(c => c.StartTime).Map(Project).ToList();

        string path = version.MediaFiles?.FirstOrDefault()?.Path;
        string sortTitle = null;
        string originalTitle = null;
        int? year = null;
        string contentRating = null;
        string plot = null;
        DateTime? dateAdded = null;
        DateTime? dateUpdated = null;

        switch (mediaItem)
        {
            case Movie m:
                var mm = m.MovieMetadata?.FirstOrDefault();
                if (mm != null)
                {
                    if (!string.IsNullOrWhiteSpace(mm.Title)) displayTitle = mm.Title;
                    sortTitle = mm.SortTitle;
                    originalTitle = mm.OriginalTitle;
                    year = mm.Year;
                    contentRating = mm.ContentRating;
                    plot = mm.Plot;
                    dateAdded = mm.DateAdded;
                    dateUpdated = mm.DateUpdated;
                }
                break;
            case Episode e:
                var em = e.EpisodeMetadata?.FirstOrDefault();
                if (em != null)
                {
                    if (!string.IsNullOrWhiteSpace(em.Title)) displayTitle = em.Title;
                    sortTitle = em.SortTitle;
                    originalTitle = em.OriginalTitle;
                    year = em.Year;
                    plot = em.Plot;
                    dateAdded = em.DateAdded;
                    dateUpdated = em.DateUpdated;
                }
                var sm = e.Season?.Show?.ShowMetadata?.FirstOrDefault();
                if (sm != null)
                {
                    contentRating = sm.ContentRating;
                }
                break;
            case OtherVideo ov:
                var ovm = ov.OtherVideoMetadata?.FirstOrDefault();
                if (ovm != null)
                {
                    if (!string.IsNullOrWhiteSpace(ovm.Title)) displayTitle = ovm.Title;
                    sortTitle = ovm.SortTitle;
                    originalTitle = ovm.OriginalTitle;
                    year = ovm.Year;
                    contentRating = ovm.ContentRating;
                    plot = ovm.Plot;
                    dateAdded = ovm.DateAdded;
                    dateUpdated = ovm.DateUpdated;
                }
                break;
            case MusicVideo mv:
                var mvm = mv.MusicVideoMetadata?.FirstOrDefault();
                if (mvm != null)
                {
                    if (!string.IsNullOrWhiteSpace(mvm.Title)) displayTitle = mvm.Title;
                    sortTitle = mvm.SortTitle;
                    originalTitle = mvm.OriginalTitle;
                    year = mvm.Year;
                    plot = mvm.Plot;
                    dateAdded = mvm.DateAdded;
                    dateUpdated = mvm.DateUpdated;
                }
                break;
            case Song s:
                var songm = s.SongMetadata?.FirstOrDefault();
                if (songm != null)
                {
                    if (!string.IsNullOrWhiteSpace(songm.Title)) displayTitle = songm.Title;
                    sortTitle = songm.SortTitle;
                    originalTitle = songm.OriginalTitle;
                    year = songm.Year;
                    dateAdded = songm.DateAdded;
                    dateUpdated = songm.DateUpdated;
                }
                break;
        }

        return new MediaItemInfo(
            mediaItem.Id,
            displayTitle,
            mediaItem.GetType().Name,
            mediaItem.LibraryPath.Library.GetType().Name,
            serverName,
            mediaItem.LibraryPath.Library.Name,
            mediaItem.State,
            version.Duration,
            version.SampleAspectRatio,
            version.DisplayAspectRatio,
            version.RFrameRate,
            version.VideoScanKind,
            version.InterlacedRatio,
            version.Width,
            version.Height,
            allStreams,
            allChapters,
            path,
            sortTitle,
            originalTitle,
            year,
            contentRating,
            plot,
            dateAdded,
            dateUpdated);
    }

    private static MediaItemInfoStream Project(MediaStream mediaStream) =>
        new(
            mediaStream.Index,
            mediaStream.MediaStreamKind,
            mediaStream.Title,
            mediaStream.Codec,
            mediaStream.Profile,
            mediaStream.Language,
            mediaStream.Channels > 0 ? mediaStream.Channels : null,
            mediaStream.Default ? true : null,
            mediaStream.Forced ? true : null,
            mediaStream.AttachedPic ? true : null,
            mediaStream.PixelFormat,
            mediaStream.ColorRange,
            mediaStream.ColorSpace,
            mediaStream.ColorTransfer,
            mediaStream.ColorPrimaries,
            mediaStream.DvProfile,
            mediaStream.MediaStreamKind is MediaStreamKind.Video ? mediaStream.HasHdr10Metadata : null,
            mediaStream.Rotation,
            mediaStream.BitsPerRawSample > 0 ? mediaStream.BitsPerRawSample : null,
            mediaStream.MimeType) { FileName = mediaStream.FileName };

    private static MediaItemInfoStream ProjectToStream(Subtitle subtitle) =>
        new(
            null,
            MediaStreamKind.ExternalSubtitle,
            subtitle.Title,
            subtitle.Codec,
            null,
            subtitle.Language,
            null,
            subtitle.Default ? true : null,
            subtitle.Forced ? true : null,
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null,
            null)
        {
            FileName = string.IsNullOrWhiteSpace(subtitle.Path) ? null : Path.GetFileName(subtitle.Path)
        };

    private static MediaItemInfoChapter Project(MediaChapter chapter) =>
        new(chapter.Title, chapter.StartTime, chapter.EndTime);
}
