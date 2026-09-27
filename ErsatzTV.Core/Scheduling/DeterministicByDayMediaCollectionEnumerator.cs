using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Extensions;
using ErsatzTV.Core.Interfaces.Scheduling;
using LanguageExt.UnsafeValueAccess;
using System.Globalization;

namespace ErsatzTV.Core.Scheduling;

public class DeterministicByDayMediaCollectionEnumerator : IMediaCollectionEnumerator
{
    private readonly CancellationToken _cancellationToken;
    private readonly Lazy<Option<TimeSpan>> _lazyMinimumDuration;
    private readonly int _mediaItemCount;
    private readonly IList<GroupedMediaItem> _mediaItems;
    private CloneableRandom _random;
    private IList<MediaItem> _shuffled;
    private DateTime? _lastDate;

    public DeterministicByDayMediaCollectionEnumerator(
        IList<GroupedMediaItem> mediaItems,
        CollectionEnumeratorState state,
        CancellationToken cancellationToken)
    {
        CurrentIncludeInProgramGuide = Option<bool>.None;

        _mediaItemCount = mediaItems.Sum(i => 1 + Optional(i.Additional).Flatten().Count());
        _mediaItems = mediaItems;
        _cancellationToken = cancellationToken;

        // Default to Today for the initial state if no MoveNext is called yet
        _lastDate = DateTime.Today;
        _random = new CloneableRandom(GetSeedFromDate(_lastDate.Value));
        _shuffled = Shuffle(_mediaItems, _random);
        
        _lazyMinimumDuration =
            new Lazy<Option<TimeSpan>>(() =>
                _shuffled.Bind(i => i.GetNonZeroDuration()).OrderBy(identity).HeadOrNone());

        State = new CollectionEnumeratorState { Seed = state.Seed, Started = state.Started };
        while (State.Index < state.Index)
        {
            MoveNext(Option<DateTimeOffset>.None);
        }
    }

    public void ResetState(CollectionEnumeratorState state)
    {
        State.Seed = state.Seed;
        State.Index = state.Index;
        State.Started = state.Started;
    }

    public string SchedulingContextName => "DeterministicByDay";

    public CollectionEnumeratorState State { get; }

    public Option<MediaItem> Current => _shuffled.Any() ? _shuffled[State.Index % _mediaItemCount] : None;
    public Option<bool> CurrentIncludeInProgramGuide { get; }

    public void MoveNext(Option<DateTimeOffset> scheduledAt)
    {
        if (_mediaItemCount == 0)
        {
            return;
        }

        DateTime currentDate = scheduledAt.Map(s => s.Date).IfNone(DateTime.Today);
        if (_lastDate != currentDate)
        {
            _lastDate = currentDate;
            _random = new CloneableRandom(GetSeedFromDate(currentDate));
            _shuffled = Shuffle(_mediaItems, _random);
        }

        State.Index++;
        if (_mediaItemCount > 0)
        {
            State.Index %= _mediaItemCount;
        }
        State.Started = true;
    }

    public Option<TimeSpan> MinimumDuration => _lazyMinimumDuration.Value;

    public int Count => _shuffled.Count;

    private static int GetSeedFromDate(DateTime date)
    {
        // Use a consistent hash for the date to generate a reproducible seed
        return date.ToString("yyyyMMdd", CultureInfo.InvariantCulture).GetHashCode();
    }

    private IList<MediaItem> Shuffle(IEnumerable<GroupedMediaItem> list, CloneableRandom random)
    {
        GroupedMediaItem[] copy = list.ToArray();

        int n = copy.Length;
        while (n > 1)
        {
            n--;
            int k = random.Next(n + 1);
            (copy[k], copy[n]) = (copy[n], copy[k]);
        }

        return GroupedMediaItem.FlattenGroups(copy, _mediaItemCount);
    }
}
