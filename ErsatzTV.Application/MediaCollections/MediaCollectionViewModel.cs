using ErsatzTV.Application.MediaCards;
using ErsatzTV.Core.Domain;

namespace ErsatzTV.Application.MediaCollections;

public record MediaCollectionViewModel(
    CollectionType CollectionType,
    int Id,
    string Name,
    bool UseCustomPlaybackOrder,
    MediaItemState State,
    int ItemCount = 0) : MediaCardViewModel(
    Id,
    Name,
    string.Empty,
    Name,
    string.Empty,
    State,
    HasMediaInfo: false);
