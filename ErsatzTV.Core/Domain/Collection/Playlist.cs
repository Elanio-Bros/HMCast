namespace ErsatzTV.Core.Domain;

public class Playlist
{
    public int Id { get; set; }
    public string Name { get; set; }
    public bool IsSystem { get; set; }

    public ICollection<PlaylistItem> Items { get; set; }
}
