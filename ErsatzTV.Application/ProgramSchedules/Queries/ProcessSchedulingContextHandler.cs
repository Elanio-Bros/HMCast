using System.Text.Json;
using System.Text.Json.Serialization;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Scheduling;
using ErsatzTV.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using JsonSerializer = System.Text.Json.JsonSerializer;

namespace ErsatzTV.Application.ProgramSchedules;

public class ProcessSchedulingContextHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<ProcessSchedulingContext, Option<string>>
{
    private static readonly JsonSerializerOptions Options = new()
    {
        Converters = { new JsonStringEnumConverter() },
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        WriteIndented = true
    };

    public async Task<Option<string>> Handle(ProcessSchedulingContext request, CancellationToken cancellationToken)
    {
        try
        {
            using JsonDocument doc = JsonDocument.Parse(request.SerializedContext);
            if (doc.RootElement.TryGetProperty(nameof(ClassicSchedulingContext.ScheduleId), out _))
            {
                var classicContext = JsonSerializer.Deserialize<ClassicSchedulingContext>(request.SerializedContext, Options);
                if (classicContext is not null && classicContext.ScheduleId > 0)
                {
                    return await GetClassicDetails(classicContext, cancellationToken);
                }
            }
        }
        catch (JsonException)
        {
            // not a valid json string, or not a context we can process
        }

        return request.SerializedContext;
    }

    private async Task<Option<string>> GetClassicDetails(
        ClassicSchedulingContext classicContext,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        string scheduleName = await dbContext.ProgramSchedules
            .Where(s => s.Id == classicContext.ScheduleId)
            .Select(s => s.Name)
            .SingleOrDefaultAsync(cancellationToken);

        var scheduleItem = await dbContext.ProgramScheduleItems
            .AsNoTracking()
            .AsSplitQuery()
            .Include(si => si.Collection)
            .Include(si => si.MultiCollection)
            .Include(si => si.Playlist)
            .Include(si => si.SmartCollection)
            .SingleOrDefaultAsync(si => si.Id == classicContext.ItemId, cancellationToken);

        var name = "Classic";
        ClassicContextFiller filler = null;
        if (classicContext.FillerPresetId is > 0)
        {
            name = "Classic - Filler";

            var fillerPreset = await dbContext.FillerPresets
                .AsNoTracking()
                .AsSplitQuery()
                .Include(p => p.Collection)
                .Include(p => p.MultiCollection)
                .Include(p => p.Playlist)
                .Include(p => p.SmartCollection)
                .SingleOrDefaultAsync(p => p.Id == classicContext.FillerPresetId, cancellationToken);

            if (fillerPreset is not null)
            {
                string collectionName = fillerPreset.CollectionType switch
                {
                    CollectionType.Collection => fillerPreset.Collection.Name,
                    CollectionType.MultiCollection => fillerPreset.MultiCollection.Name,
                    CollectionType.Playlist => fillerPreset.Playlist.Name,
                    CollectionType.SmartCollection => fillerPreset.SmartCollection.Name,
                    _ => null
                };

                filler = new ClassicContextFiller(
                    fillerPreset.Id,
                    fillerPreset.Name,
                    fillerPreset.FillerKind,
                    fillerPreset.FillerMode,
                    fillerPreset.CollectionType,
                    collectionName);
            }
        }

        ClassicContextScheduleItem item;
        if (scheduleItem is not null)
        {
            string collectionName = scheduleItem.CollectionType switch
            {
                CollectionType.Collection => scheduleItem.Collection.Name,
                CollectionType.MultiCollection => scheduleItem.MultiCollection.Name,
                CollectionType.Playlist => scheduleItem.Playlist.Name,
                CollectionType.SmartCollection => scheduleItem.SmartCollection.Name,
                _ => null
            };

            item = new ClassicContextScheduleItem(scheduleItem.Id, scheduleItem.CollectionType, collectionName);
        }
        else
        {
            item = new ClassicContextScheduleItem(classicContext.ItemId, null, null);
        }

        var context = new ClassicContext(
            new ContextScheduler(name, classicContext.Scheduler),
            new ClassicContextSchedule(classicContext.ScheduleId, scheduleName ?? string.Empty),
            item,
            filler,
            new ContextEnumerator(classicContext.Enumerator, classicContext.Seed, classicContext.Index));

        return JsonSerializer.Serialize(context, Options);
    }

    private sealed record ClassicContext(
        ContextScheduler Scheduler,
        ClassicContextSchedule Schedule,
        ClassicContextScheduleItem ScheduleItem,
        ClassicContextFiller Filler,
        ContextEnumerator Enumerator);

    private sealed record ContextScheduler(string Type, string Mode);

    private sealed record ClassicContextSchedule(int Id, string Name);

    private sealed record ClassicContextScheduleItem(int Id, CollectionType? CollectionType, string CollectionName);

    private sealed record ClassicContextFiller(
        int Id,
        string Name,
        FillerKind Kind,
        FillerMode Mode,
        CollectionType CollectionType,
        string CollectionName);

    private sealed record ContextEnumerator(string Name, int Seed, int Index);
}
