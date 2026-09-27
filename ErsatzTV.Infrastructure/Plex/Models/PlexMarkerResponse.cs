using System.Xml.Serialization;

namespace ErsatzTV.Infrastructure.Plex.Models;

public class PlexMarkerResponse
{
    [XmlAttribute("id")]
    public int Id { get; set; }

    [XmlAttribute("type")]
    public string Type { get; set; }

    [XmlAttribute("startTimeOffset")]
    public int StartTimeOffset { get; set; }

    [XmlAttribute("endTimeOffset")]
    public int EndTimeOffset { get; set; }
}
