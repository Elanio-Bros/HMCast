namespace ErsatzTV.Core.Domain;

public class ProgramScheduleItemCommercial
{
    public int Id { get; set; }

    public int ProgramScheduleItemId { get; set; }
    public ProgramScheduleItem ProgramScheduleItem { get; set; }

    public int CommercialPresetId { get; set; }
    public CommercialPreset CommercialPreset { get; set; }

    public CommercialBreakPlacement Placement { get; set; }
}
