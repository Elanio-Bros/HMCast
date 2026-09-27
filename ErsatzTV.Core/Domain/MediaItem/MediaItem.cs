namespace ErsatzTV.Core.Domain;

public abstract class MediaItem
{
    public int Id { get; set; }
    public int LibraryPathId { get; set; }
    public LibraryPath LibraryPath { get; set; }
    public List<Collection> Collections { get; set; }
    public List<CollectionItem> CollectionItems { get; set; }
    public List<TraktListItem> TraktListItems { get; set; }
    public List<MediaSkip> MediaSkips { get; set; }
    public bool ShowIntro { get; set; } = true;
    public bool ShowFinish { get; set; } = true;
    public bool ShowPreview { get; set; } = true;
    public bool ShowRecap { get; set; } = true;
    public bool ShowCut { get; set; }
    public MediaItemState State { get; set; }
}
