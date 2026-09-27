using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Scheduling;
using NUnit.Framework;
using Shouldly;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace ErsatzTV.Core.Tests.Scheduling;

[TestFixture]
public class DeterministicByDayEnumeratorTests
{
    [SetUp]
    public void SetUp() => _cancellationToken = new CancellationTokenSource(TimeSpan.FromSeconds(10)).Token;

    private CancellationToken _cancellationToken;

    [Test]
    public void Same_Date_Should_Yield_Same_Shuffle()
    {
        List<MediaItem> contents = Episodes(10);
        var state = new CollectionEnumeratorState();
        var groupedMediaItems = contents.Map(mi => new GroupedMediaItem(mi, null)).ToList();

        // Instance 1
        var enumerator1 = new DeterministicByDayMediaCollectionEnumerator(groupedMediaItems, state, _cancellationToken);
        
        // Instance 2
        var enumerator2 = new DeterministicByDayMediaCollectionEnumerator(groupedMediaItems, state, _cancellationToken);

        var list1 = new List<int>();
        var list2 = new List<int>();

        var testDate = new DateTimeOffset(2023, 10, 15, 12, 0, 0, TimeSpan.Zero);

        for (var i = 1; i <= 10; i++)
        {
            enumerator1.MoveNext(testDate);
            enumerator1.Current.Do(x => list1.Add(x.Id));

            enumerator2.MoveNext(testDate);
            enumerator2.Current.Do(x => list2.Add(x.Id));
        }

        list1.ShouldBe(list2); // Both instances given the same date should produce exact same shuffle
    }

    [Test]
    public void Different_Date_Should_Yield_Different_Shuffle()
    {
        List<MediaItem> contents = Episodes(10);
        var state = new CollectionEnumeratorState();
        var groupedMediaItems = contents.Map(mi => new GroupedMediaItem(mi, null)).ToList();

        var enumerator = new DeterministicByDayMediaCollectionEnumerator(groupedMediaItems, state, _cancellationToken);

        var listDay1 = new List<int>();
        var listDay2 = new List<int>();

        var testDate1 = new DateTimeOffset(2023, 10, 15, 12, 0, 0, TimeSpan.Zero);
        var testDate2 = new DateTimeOffset(2023, 10, 16, 12, 0, 0, TimeSpan.Zero); // Next Day

        // Drain Day 1
        for (var i = 1; i <= 10; i++)
        {
            enumerator.MoveNext(testDate1);
            enumerator.Current.Do(x => listDay1.Add(x.Id));
        }

        // Drain Day 2 (should detect date change and reshuffle)
        for (var i = 1; i <= 10; i++)
        {
            enumerator.MoveNext(testDate2);
            enumerator.Current.Do(x => listDay2.Add(x.Id));
        }

        listDay1.ShouldNotBe(listDay2); // Shuffles should be different
        listDay1.ShouldBe([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], true); // Should contain all items
        listDay2.ShouldBe([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], true); // Should contain all items
    }

    private static List<MediaItem> Episodes(int count) =>
        Enumerable.Range(1, count).Select(i => (MediaItem)new Episode
            {
                Id = i,
                EpisodeMetadata = new List<EpisodeMetadata>
                {
                    new()
                    {
                        ReleaseDate = new DateTime(2020, 1, i)
                    }
                }
            })
            .Reverse()
            .ToList();
}
