namespace ErsatzTV.Core.Domain;

public class PlaylistItemCommercial
{
    public int Id { get; set; }

    public int PlaylistItemId { get; set; }
    public PlaylistItem PlaylistItem { get; set; }

    public int CommercialPresetId { get; set; }
    public CommercialPreset CommercialPreset { get; set; }

    public CommercialBreakPlacement Placement { get; set; }
}
