using System.Collections.Generic;

namespace ErsatzTV.Core.Domain;

public class ScreenLayout
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string AspectRatio { get; set; } = "16:9";
    public List<ScreenLayoutElement> Elements { get; set; } = new();
    public List<ScreenLayoutRule> Rules { get; set; } = new();
}
