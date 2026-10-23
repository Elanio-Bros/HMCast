namespace ErsatzTV.Core.Domain;

public class ScreenLayoutRule
{
    public int Id { get; set; }
    public int ScreenLayoutId { get; set; }
    public ScreenLayout ScreenLayout { get; set; }

    public int ElementId { get; set; }
    public ScreenLayoutElement Element { get; set; }

    public ScreenLayoutRuleTrigger Trigger { get; set; }
    public ScreenLayoutRuleAction Action { get; set; }
    public int OffsetSeconds { get; set; }
    public int DurationSeconds { get; set; }
}
