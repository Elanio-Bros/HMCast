using ErsatzTV.Core.Domain;

namespace ErsatzTV.Application.Scheduling;

internal static class Mapper
{
    internal static PlayoutItemPreviewViewModel ProjectToViewModel(PlayoutItem playoutItem) =>
        new(
            Playouts.Mapper.GetDisplayTitle(playoutItem.MediaItem, playoutItem.ChapterTitle),
            playoutItem.StartOffset.TimeOfDay,
            playoutItem.FinishOffset.TimeOfDay,
            playoutItem.GetDisplayDuration());
}
