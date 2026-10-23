using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Domain.Filler;
using ErsatzTV.Core.Interfaces.Streaming;
using LanguageExt;
using Microsoft.Extensions.Logging;

namespace ErsatzTV.Core.Streaming;

public class ScreenLayoutEngine : IScreenLayoutEngine
{
    private readonly ILogger<ScreenLayoutEngine> _logger;

    public ScreenLayoutEngine(ILogger<ScreenLayoutEngine> logger)
    {
        _logger = logger;
    }

    public Option<ScreenLayout> ResolveActiveLayout(Playout playout, Channel channel)
    {
        if (playout?.ScreenLayout != null)
        {
            return Option<ScreenLayout>.Some(playout.ScreenLayout);
        }

        if (channel?.ScreenLayout != null)
        {
            return Option<ScreenLayout>.Some(channel.ScreenLayout);
        }

        return Option<ScreenLayout>.None;
    }

    public ScreenLayoutFilterResult GenerateFilterSteps(
        ScreenLayout layout,
        PlayoutItem playoutItem,
        DateTimeOffset now,
        int videoWidth,
        int videoHeight)
    {
        var filterSteps = new List<string>();
        var inputs = new List<string>();

        if (layout == null || layout.Elements == null || layout.Elements.Count == 0)
        {
            return new ScreenLayoutFilterResult(filterSteps, inputs);
        }

        TimeSpan itemOffset = now > playoutItem.Start ? now - playoutItem.Start : TimeSpan.Zero;
        TimeSpan itemDuration = playoutItem.Finish > playoutItem.Start ? playoutItem.Finish - playoutItem.Start : TimeSpan.Zero;
        bool isCommercial = playoutItem.FillerKind != FillerKind.None;

        List<ScreenLayoutElement> elements = layout.Elements.OrderBy(e => e.ZIndex).ToList();

        foreach (ScreenLayoutElement element in elements)
        {
            // Avaliar regras aplicáveis ao elemento
            List<ScreenLayoutRule> rules = layout.Rules?.Where(r => r.ElementId == element.Id).ToList() ?? new List<ScreenLayoutRule>();
            bool isHidden = false;
            double? timeWindowStart = null;
            double? timeWindowEnd = null;

            foreach (ScreenLayoutRule rule in rules)
            {
                switch (rule.Trigger)
                {
                    case ScreenLayoutRuleTrigger.Always:
                        if (rule.Action == ScreenLayoutRuleAction.Hide)
                        {
                            isHidden = true;
                        }
                        break;

                    case ScreenLayoutRuleTrigger.CommercialBreak:
                        if (isCommercial && rule.Action == ScreenLayoutRuleAction.Hide)
                        {
                            isHidden = true;
                        }
                        break;

                    case ScreenLayoutRuleTrigger.ProgramStart:
                        if (rule.Action == ScreenLayoutRuleAction.Hide)
                        {
                            if (itemOffset.TotalSeconds >= rule.OffsetSeconds &&
                                itemOffset.TotalSeconds <= rule.OffsetSeconds + rule.DurationSeconds)
                            {
                                isHidden = true;
                            }
                        }
                        else if (rule.Action == ScreenLayoutRuleAction.Show)
                        {
                            timeWindowStart = rule.OffsetSeconds;
                            timeWindowEnd = rule.OffsetSeconds + rule.DurationSeconds;
                        }
                        break;

                    case ScreenLayoutRuleTrigger.ProgramEnd:
                        double endThreshold = Math.Max(0, itemDuration.TotalSeconds - rule.DurationSeconds - rule.OffsetSeconds);
                        if (rule.Action == ScreenLayoutRuleAction.Hide)
                        {
                            if (itemOffset.TotalSeconds >= endThreshold)
                            {
                                isHidden = true;
                            }
                        }
                        else if (rule.Action == ScreenLayoutRuleAction.Show)
                        {
                            timeWindowStart = endThreshold;
                            timeWindowEnd = itemDuration.TotalSeconds;
                        }
                        break;
                }
            }

            if (isHidden)
            {
                continue;
            }

            // Normalizar coordenadas para a resolução de saída
            int posX = element.X <= 1.0 && element.X > 0 ? (int)(element.X * videoWidth) : (int)element.X;
            int posY = element.Y <= 1.0 && element.Y > 0 ? (int)(element.Y * videoHeight) : (int)element.Y;
            int width = element.Width <= 1.0 && element.Width > 0 ? (int)(element.Width * videoWidth) : (int)element.Width;
            int height = element.Height <= 1.0 && element.Height > 0 ? (int)(element.Height * videoHeight) : (int)element.Height;

            double opacity = Math.Clamp(element.Opacity, 0.0, 1.0);
            string opacityStr = opacity.ToString("F2", CultureInfo.InvariantCulture);

            switch (element.ElementType)
            {
                case ScreenLayoutElementType.LogoWatermark:
                case ScreenLayoutElementType.ImageOverlay:
                    if (!string.IsNullOrWhiteSpace(element.ContentPath))
                    {
                        inputs.Add(element.ContentPath);
                        string filter = $"overlay=x={posX}:y={posY}";

                        if (timeWindowStart.HasValue && timeWindowEnd.HasValue)
                        {
                            string tStart = timeWindowStart.Value.ToString("F1", CultureInfo.InvariantCulture);
                            string tEnd = timeWindowEnd.Value.ToString("F1", CultureInfo.InvariantCulture);
                            filter += $":enable='between(t,{tStart},{tEnd})'";
                        }

                        filterSteps.Add(filter);
                    }
                    break;

                case ScreenLayoutElementType.TextBanner:
                    if (!string.IsNullOrWhiteSpace(element.TextContent))
                    {
                        string safeText = element.TextContent.Replace("'", "\\'").Replace(":", "\\:");
                        string drawtext = $"drawtext=text='{safeText}':x={posX}:y={posY}:fontsize=24:fontcolor=white:alpha={opacityStr}";

                        if (timeWindowStart.HasValue && timeWindowEnd.HasValue)
                        {
                            string tStart = timeWindowStart.Value.ToString("F1", CultureInfo.InvariantCulture);
                            string tEnd = timeWindowEnd.Value.ToString("F1", CultureInfo.InvariantCulture);
                            drawtext += $":enable='between(t,{tStart},{tEnd})'";
                        }

                        filterSteps.Add(drawtext);
                    }
                    break;

                case ScreenLayoutElementType.CustomHtml:
                    _logger.LogDebug("CustomHtml layout element {Name} ignored for direct ffmpeg filter", element.Name);
                    break;
            }
        }

        return new ScreenLayoutFilterResult(filterSteps, inputs);
    }
}
