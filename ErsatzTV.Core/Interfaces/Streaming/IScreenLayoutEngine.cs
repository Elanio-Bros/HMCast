using System;
using System.Collections.Generic;
using ErsatzTV.Core.Domain;
using LanguageExt;

namespace ErsatzTV.Core.Interfaces.Streaming;

public record ScreenLayoutFilterResult(
    List<string> FilterComplexSteps,
    List<string> AdditionalInputs);

public interface IScreenLayoutEngine
{
    Option<ScreenLayout> ResolveActiveLayout(Playout playout, Channel channel);

    ScreenLayoutFilterResult GenerateFilterSteps(
        ScreenLayout layout,
        PlayoutItem playoutItem,
        DateTimeOffset now,
        int videoWidth,
        int videoHeight);
}
