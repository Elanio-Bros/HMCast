using System.ComponentModel.DataAnnotations.Schema;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Scheduling;
using Newtonsoft.Json;

namespace ErsatzTV.Core.Domain;

public abstract class ProgramScheduleItem
{
    public int Id { get; set; }
    public int Index { get; set; }
    private StartType? _startType;
    public StartType StartType
    {
        get => _startType ?? (StartTime.HasValue ? StartType.Fixed : StartType.Dynamic);
        set => _startType = value;
    }
    public TimeSpan? StartTime { get; set; }
    public FixedStartTimeBehavior? FixedStartTimeBehavior { get; set; }

    // Duração & Fechamento
    public ScheduleItemDurationMode DurationMode { get; set; }
    public TimeSpan? TargetDuration { get; set; }

    // Quantidade de Itens (Unificado: substitui a divisão One vs Multiple)
    public int? ItemCount { get; set; }

    [NotMapped]
    public int? Count
    {
        get => ItemCount;
        set => ItemCount = value;
    }

    // Integração Nativa de Cutouts (MediaSkip)
    public bool RespectMediaSkipChapters { get; set; } = true;
    public bool FillCommercialGapsWithFillers { get; set; } = true;

    // Layout de Tela Específico desta Faixa
    public int? ScreenLayoutId { get; set; }
    public ScreenLayout ScreenLayout { get; set; }

    // Gestão de Comerciais Integrada
    public List<ProgramScheduleItemCommercial> Commercials { get; set; } = new();

    public CollectionType CollectionType { get; set; }
    public GuideMode GuideMode { get; set; }
    public string CustomTitle { get; set; }
    public int ProgramScheduleId { get; set; }

    [JsonIgnore]
    public ProgramSchedule ProgramSchedule { get; set; }

    public int? CollectionId { get; set; }
    public Collection Collection { get; set; }
    public int? MediaItemId { get; set; }
    public MediaItem MediaItem { get; set; }
    public int? MultiCollectionId { get; set; }
    public MultiCollection MultiCollection { get; set; }
    public int? SmartCollectionId { get; set; }
    public SmartCollection SmartCollection { get; set; }
    public string SearchTitle { get; set; }
    public string SearchQuery { get; set; }
    public int? PlaylistId { get; set; }
    public Playlist Playlist { get; set; }
    public string FakeCollectionKey { get; set; }
    public PlaybackOrder PlaybackOrder { get; set; }
    public MarathonGroupBy MarathonGroupBy { get; set; }
    public bool MarathonShuffleGroups { get; set; }
    public bool MarathonShuffleItems { get; set; }
    public int? MarathonBatchSize { get; set; }
    public int? PreRollFillerId { get; set; }
    public FillerPreset PreRollFiller { get; set; }
    public int? MidRollFillerId { get; set; }
    public FillerPreset MidRollFiller { get; set; }
    public int? PostRollFillerId { get; set; }
    public FillerPreset PostRollFiller { get; set; }
    public int? TailFillerId { get; set; }
    public FillerPreset TailFiller { get; set; }
    public int? FallbackFillerId { get; set; }
    public FillerPreset FallbackFiller { get; set; }
    public List<ChannelWatermark> Watermarks { get; set; }
    public List<ProgramScheduleItemWatermark> ProgramScheduleItemWatermarks { get; set; }
    public List<GraphicsElement> GraphicsElements { get; set; }
    public List<ProgramScheduleItemGraphicsElement> ProgramScheduleItemGraphicsElements { get; set; }
    public string PreferredAudioLanguageCode { get; set; }
    public string PreferredAudioTitle { get; set; }
    public string PreferredSubtitleLanguageCode { get; set; }
    public ChannelSubtitleMode? SubtitleMode { get; set; }
    public FillWithGroupMode FillWithGroupMode { get; set; }
}
