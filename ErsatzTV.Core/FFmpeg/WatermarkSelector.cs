using System.IO.Abstractions;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Domain.Scheduling;
using ErsatzTV.Core.Images;
using ErsatzTV.Core.Interfaces.FFmpeg;
using ErsatzTV.Core.Interfaces.Images;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace ErsatzTV.Core.FFmpeg;

public class WatermarkSelector(
    IFileSystem fileSystem,
    IImageCache imageCache,
    ILogger<WatermarkSelector> logger)
    : IWatermarkSelector
{
    public List<WatermarkOptions> SelectWatermarks(
        Option<ChannelWatermark> globalWatermark,
        Channel channel,
        PlayoutItem playoutItem,
        DateTimeOffset now,
        bool shouldLogMessages)
    {
        ILogger<WatermarkSelector> log = shouldLogMessages ? logger : NullLogger<WatermarkSelector>.Instance;

        log.LogDebug("Checking for watermark at {Now}", now);

        var result = new List<WatermarkOptions>();

        if (channel.StreamingMode == StreamingMode.HttpLiveStreamingDirect)
        {
            return result;
        }

        if (playoutItem.DisableWatermarks)
        {
            log.LogDebug("Watermark is disabled by playout item");
            return result;
        }

        if (playoutItem.Watermarks.Count > 0)
        {
            foreach (var watermark in playoutItem.Watermarks)
            {
                Option<WatermarkOptions> options = GetWatermarkOptions(
                    channel,
                    watermark,
                    Option<ChannelWatermark>.None,
                    shouldLogMessages);
                result.AddRange(options);
            }

            return result;
        }


        Option<WatermarkOptions> finalOptions = GetWatermarkOptions(
            channel,
            Option<ChannelWatermark>.None,
            globalWatermark,
            shouldLogMessages);
        result.AddRange(finalOptions);

        return result;
    }

    public Option<WatermarkOptions> GetWatermarkOptions(
        Channel channel,
        Option<ChannelWatermark> playoutItemWatermark,
        Option<ChannelWatermark> globalWatermark,
        bool shouldLogMessages)
    {
        ILogger<WatermarkSelector> log = shouldLogMessages ? logger : NullLogger<WatermarkSelector>.Instance;

        if (channel.StreamingMode == StreamingMode.HttpLiveStreamingDirect)
        {
            return Option<WatermarkOptions>.None;
        }

        // check for playout item watermark
        foreach (ChannelWatermark watermark in playoutItemWatermark)
        {
            switch (watermark.ImageSource)
            {
                // used for song progress overlay
                case ChannelWatermarkImageSource.Resource:
                    string resourcePath = fileSystem.Path.Combine(
                        FileSystemLayout.ResourcesCacheFolder,
                        watermark.Image);
                    if (fileSystem.File.Exists(resourcePath))
                    {
                        return new WatermarkOptions(watermark, resourcePath, Option<int>.None);
                    }

                    log.LogWarning(
                        "Watermark resource no longer exists at {Path} and will be ignored",
                        resourcePath);
                    return None;
                case ChannelWatermarkImageSource.Custom:
                    // bad form validation makes this possible
                    if (string.IsNullOrWhiteSpace(watermark.Image))
                    {
                        log.LogWarning(
                            "Watermark {Name} has custom image configured with no image; ignoring",
                            watermark.Name);
                        break;
                    }

                    log.LogDebug("Watermark will come from playout item (custom)");

                    string customPath = imageCache.GetPathForImage(
                        watermark.Image,
                        ArtworkKind.Watermark,
                        Option<int>.None);

                    if (fileSystem.File.Exists(customPath))
                    {
                        return new WatermarkOptions(watermark, customPath, None);
                    }

                    log.LogWarning(
                        "Custom watermark no longer exists at {Path} and will be ignored",
                        customPath);
                    return None;
                case ChannelWatermarkImageSource.ChannelLogo:
                    log.LogDebug("Watermark will come from playout item (channel logo)");

                    string channelPath = ChannelLogoGenerator.GenerateChannelLogoUrl(channel);
                    Option<Artwork> maybeLogoArtwork =
                        Optional(channel.Artwork.Find(a => a.ArtworkKind == ArtworkKind.Logo));
                    foreach (var logoArtwork in maybeLogoArtwork)
                    {
                        channelPath = Artwork.IsExternalUrl(logoArtwork.Path)
                            ? logoArtwork.Path
                            : imageCache.GetPathForImage(logoArtwork.Path, ArtworkKind.Logo, Option<int>.None);
                    }

                    // urls (external logos, generated channel logos) can't be checked on the file system
                    if (Artwork.IsExternalUrl(channelPath) || fileSystem.File.Exists(channelPath))
                    {
                        return new WatermarkOptions(watermark, channelPath, None);
                    }

                    log.LogWarning(
                        "Channel logo no longer exists at {Path} and will be ignored",
                        channelPath);
                    return None;
                default:
                    throw new NotSupportedException("Unsupported watermark image source");
            }
        }

        // check for channel watermark
        if (channel.Watermark != null)
        {
            switch (channel.Watermark.ImageSource)
            {
                case ChannelWatermarkImageSource.Custom:
                    log.LogDebug("Watermark will come from channel (custom)");

                    string customPath = imageCache.GetPathForImage(
                        channel.Watermark.Image,
                        ArtworkKind.Watermark,
                        Option<int>.None);

                    if (fileSystem.File.Exists(customPath))
                    {
                        return new WatermarkOptions(channel.Watermark, customPath, None);
                    }

                    log.LogWarning(
                        "Custom watermark no longer exists at {Path} and will be ignored",
                        customPath);
                    return None;
                case ChannelWatermarkImageSource.ChannelLogo:
                    log.LogDebug("Watermark will come from channel (channel logo)");

                    string channelPath = ChannelLogoGenerator.GenerateChannelLogoUrl(channel);
                    Option<Artwork> maybeLogoArtwork =
                        Optional(channel.Artwork.Find(a => a.ArtworkKind == ArtworkKind.Logo));
                    foreach (var logoArtwork in maybeLogoArtwork)
                    {
                        channelPath = Artwork.IsExternalUrl(logoArtwork.Path)
                            ? logoArtwork.Path
                            : imageCache.GetPathForImage(logoArtwork.Path, ArtworkKind.Logo, Option<int>.None);
                    }

                    // urls (external logos, generated channel logos) can't be checked on the file system
                    if (Artwork.IsExternalUrl(channelPath) || fileSystem.File.Exists(channelPath))
                    {
                        return new WatermarkOptions(channel.Watermark, channelPath, None);
                    }

                    log.LogWarning(
                        "Channel logo no longer exists at {Path} and will be ignored",
                        channelPath);
                    return None;
                default:
                    throw new NotSupportedException("Unsupported watermark image source");
            }
        }

        // check for global watermark
        foreach (ChannelWatermark watermark in globalWatermark)
        {
            switch (watermark.ImageSource)
            {
                case ChannelWatermarkImageSource.Custom:
                    log.LogDebug("Watermark will come from global (custom)");

                    string customPath = imageCache.GetPathForImage(
                        watermark.Image,
                        ArtworkKind.Watermark,
                        Option<int>.None);

                    if (fileSystem.File.Exists(customPath))
                    {
                        return new WatermarkOptions(watermark, customPath, None);
                    }

                    log.LogWarning(
                        "Custom watermark no longer exists at {Path} and will be ignored",
                        customPath);
                    return None;
                case ChannelWatermarkImageSource.ChannelLogo:
                    log.LogDebug("Watermark will come from global (channel logo)");

                    string channelPath = ChannelLogoGenerator.GenerateChannelLogoUrl(channel);
                    Option<Artwork> maybeLogoArtwork =
                        Optional(channel.Artwork.Find(a => a.ArtworkKind == ArtworkKind.Logo));
                    foreach (var logoArtwork in maybeLogoArtwork)
                    {
                        channelPath = Artwork.IsExternalUrl(logoArtwork.Path)
                            ? logoArtwork.Path
                            : imageCache.GetPathForImage(logoArtwork.Path, ArtworkKind.Logo, Option<int>.None);
                    }

                    // urls (external logos, generated channel logos) can't be checked on the file system
                    if (Artwork.IsExternalUrl(channelPath) || fileSystem.File.Exists(channelPath))
                    {
                        return new WatermarkOptions(watermark, channelPath, None);
                    }

                    log.LogWarning(
                        "Channel logo no longer exists at {Path} and will be ignored",
                        channelPath);
                    return None;
                default:
                    throw new NotSupportedException("Unsupported watermark image source");
            }
        }

        return Option<WatermarkOptions>.None;
    }
}
