using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Interfaces.Metadata;

namespace ErsatzTV.Core.Scheduling;

/// <summary>
/// HMCast 3.0: Avalia quais cortes (MediaSkips) devem ser ativados para um MediaItem
/// com base nas flags de permissão (ShowIntro, etc) e no contexto da sessão (Maratona vs Troca de Show).
/// </summary>
public static class MediaSkipEvaluator
{
    public static List<MediaSkip> GetActiveSkips(
        MediaItem currentItem,
        MediaItem previousItem,
        MediaItem nextItem,
        bool isFirstItemInSession,
        bool isLastItemInSession)
    {
        if (currentItem?.MediaSkips == null || currentItem.MediaSkips.Count == 0)
        {
            return [];
        }

        bool isSameShowAsPrevious = false;
        if (previousItem != null && currentItem is Episode currentEp && previousItem is Episode prevEp)
        {
            if (currentEp.Season?.ShowId != null && prevEp.Season?.ShowId != null)
            {
                isSameShowAsPrevious = currentEp.Season.ShowId == prevEp.Season.ShowId;
            }
        }

        bool isSameShowAsNext = false;
        if (nextItem != null && currentItem is Episode currentEp2 && nextItem is Episode nextEp)
        {
            if (currentEp2.Season?.ShowId != null && nextEp.Season?.ShowId != null)
            {
                isSameShowAsNext = currentEp2.Season.ShowId == nextEp.Season.ShowId;
            }
        }

        var activeSkips = new List<MediaSkip>();

        foreach (var skip in currentItem.MediaSkips)
        {
            bool shouldKeepSkip = true;

            switch (skip.Kind)
            {
                case MediaSkipKind.Intro:
                    if (!currentItem.ShowIntro)
                    {
                        shouldKeepSkip = true; // User disabled intro entirely, so ALWAYS skip it
                    }
                    else if (isFirstItemInSession)
                    {
                        shouldKeepSkip = false; // First item: show intro (do NOT skip)
                    }
                    else if (isSameShowAsPrevious)
                    {
                        shouldKeepSkip = true; // Marathon: skip intro
                    }
                    else
                    {
                        shouldKeepSkip = false; // Show changed: show intro (do NOT skip)
                    }
                    break;

                case MediaSkipKind.Finish:
                    if (!currentItem.ShowFinish)
                    {
                        shouldKeepSkip = true; // User disabled finish entirely, so ALWAYS skip it
                    }
                    else if (isLastItemInSession)
                    {
                        shouldKeepSkip = false; // Last item: show finish (do NOT skip)
                    }
                    else if (isSameShowAsNext)
                    {
                        shouldKeepSkip = true; // Marathon: skip finish of current episode to jump to next
                    }
                    else
                    {
                        shouldKeepSkip = false; // Show will change next: show finish of this show (do NOT skip)
                    }
                    break;

                case MediaSkipKind.Preview:
                    if (!currentItem.ShowPreview)
                    {
                        shouldKeepSkip = true;
                    }
                    break;

                case MediaSkipKind.Recap:
                    if (!currentItem.ShowRecap)
                    {
                        shouldKeepSkip = true;
                    }
                    break;

                case MediaSkipKind.Cut:
                    if (!currentItem.ShowCut)
                    {
                        shouldKeepSkip = true; // User disabled the cut, so skip it (hide the cut content)
                    }
                    else
                    {
                        shouldKeepSkip = false; // User enabled the cut, so do NOT skip it (show the cut content)
                    }
                    break;
            }

            if (shouldKeepSkip)
            {
                activeSkips.Add(skip);
            }
        }

        return activeSkips;
    }
}
