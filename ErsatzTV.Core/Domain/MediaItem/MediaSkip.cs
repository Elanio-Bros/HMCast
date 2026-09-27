namespace ErsatzTV.Core.Domain;

public class MediaSkip
{
    public int Id { get; set; }
    public int MediaItemId { get; set; }
    public MediaItem MediaItem { get; set; }
    public TimeSpan Start { get; set; }
    public TimeSpan End { get; set; }
    public MediaSkipKind Kind { get; set; }
    public MediaSkipSource Source { get; set; }
}
