using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Domain.Scheduling;
using ErsatzTV.Core.Interfaces.FFmpeg;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace ErsatzTV.Core.FFmpeg;

public class GraphicsElementSelector(ILogger<GraphicsElementSelector> logger)
    : IGraphicsElementSelector
{
    public List<PlayoutItemGraphicsElement> SelectGraphicsElements(
        Channel channel,
        PlayoutItem playoutItem,
        DateTimeOffset now,
        bool shouldLogMessages)
    {
        ILogger<GraphicsElementSelector> log = shouldLogMessages
            ? logger
            : NullLogger<GraphicsElementSelector>.Instance;

        log.LogDebug("Checking for graphics elements at {Now}", now);

        var result = new List<PlayoutItemGraphicsElement>();

        if (channel.StreamingMode == StreamingMode.HttpLiveStreamingDirect)
        {
            return result;
        }

        result.AddRange(playoutItem.PlayoutItemGraphicsElements);

        return result;
    }
}
