using System;
using System.Diagnostics.CodeAnalysis;

namespace ErsatzTV.Core.Domain;

[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
public class ExternalCollection
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public ExternalCollectionProvider Provider { get; set; } = ExternalCollectionProvider.Trakt;
    public string ExternalId { get; set; }
    public string Url { get; set; }
    public bool AutoSync { get; set; } = true;
    public int SyncFrequencyHours { get; set; } = 24;
    public DateTimeOffset? LastSync { get; set; }
    public int ItemCount { get; set; }

    public int? CollectionId { get; set; }
    public Collection Collection { get; set; }
}
