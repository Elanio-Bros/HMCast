using System;
using ErsatzTV.Core.Domain;

namespace ErsatzTV.Application.Commercials;

public record CommercialPresetViewModel(
    int Id,
    string Name,
    CommercialKind Kind,
    int? CollectionId,
    string CollectionName,
    int? MediaItemId,
    string MediaItemTitle,
    TimeSpan? TargetDuration,
    int? PadSeconds,
    bool StrictDuration,
    PlaybackOrder PlaybackOrder);
