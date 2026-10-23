using System;

namespace ErsatzTV.Core.Domain;

public class CommercialPreset
{
    public int Id { get; set; }
    public string Name { get; set; }
    public CommercialKind Kind { get; set; } = CommercialKind.Filler;

    // Coleção de mídias do comercial
    public int? CollectionId { get; set; }
    public Collection Collection { get; set; }
    public int? MediaItemId { get; set; }
    public MediaItem MediaItem { get; set; }

    // Regras de preenchimento
    public TimeSpan? TargetDuration { get; set; }
    public int? PadSeconds { get; set; }
    public bool StrictDuration { get; set; }
    public PlaybackOrder PlaybackOrder { get; set; } = PlaybackOrder.Random;
}
