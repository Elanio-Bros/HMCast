using ErsatzTV.Core.Domain;

namespace ErsatzTV.Application.MediaItems;

public record MediaItemInfo(
    int Id,
    string Title,
    string Kind,
    string LibraryKind,
    string ServerName,
    string LibraryName,
    MediaItemState State,
    TimeSpan Duration,
    string SampleAspectRatio,
    string DisplayAspectRatio,
    string RFrameRate,
    VideoScanKind VideoScanKind,
    double? InterlacedRatio,
    int Width,
    int Height,
    List<MediaItemInfoStream> Streams,
    List<MediaItemInfoChapter> Chapters,
    string Path = null,
    string SortTitle = null,
    string OriginalTitle = null,
    int? Year = null,
    string ContentRating = null,
    string Plot = null,
    DateTime? DateAdded = null,
    DateTime? DateUpdated = null);
