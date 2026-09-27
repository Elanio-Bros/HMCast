using ErsatzTV.FFmpeg.Environment;

namespace ErsatzTV.FFmpeg.Filter;

public class MediaSkipFilter : BaseFilter
{
    private readonly IList<Tuple<TimeSpan, TimeSpan>> _skips;

    public MediaSkipFilter(IList<Tuple<TimeSpan, TimeSpan>> skips)
    {
        _skips = skips;
    }

    public override string Filter
    {
        get
        {
            if (_skips == null || !_skips.Any())
            {
                return string.Empty;
            }

            var betweens = _skips.Select(s => 
                $"between(t,{s.Item1.TotalSeconds.ToString(System.Globalization.CultureInfo.InvariantCulture)},{s.Item2.TotalSeconds.ToString(System.Globalization.CultureInfo.InvariantCulture)})");
            
            var condition = string.Join("+", betweens);
            
            return $"select='not({condition})',setpts=N/FRAME_RATE/TB";
        }
    }

    public string AudioFilter
    {
        get
        {
            if (_skips == null || !_skips.Any())
            {
                return string.Empty;
            }

            var betweens = _skips.Select(s => 
                $"between(t,{s.Item1.TotalSeconds.ToString(System.Globalization.CultureInfo.InvariantCulture)},{s.Item2.TotalSeconds.ToString(System.Globalization.CultureInfo.InvariantCulture)})");
            
            var condition = string.Join("+", betweens);
            
            return $"aselect='not({condition})',asetpts=N/SR/TB";
        }
    }

    public override FrameState NextState(FrameState currentState) => currentState;
}
