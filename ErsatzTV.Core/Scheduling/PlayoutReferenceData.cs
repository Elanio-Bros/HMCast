using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Scheduling;

namespace ErsatzTV.Core.Scheduling;

public record PlayoutReferenceData(
    Channel Channel,
    List<PlayoutItem> ExistingItems,
    ProgramSchedule ProgramSchedule,
    List<ProgramScheduleAlternate> ProgramScheduleAlternates,
    List<PlayoutHistory> PlayoutHistory,
    TimeSpan MaxPlayoutOffset);
