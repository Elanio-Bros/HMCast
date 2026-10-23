using System;
using System.Collections.Generic;
using ErsatzTV.Core.Domain;
using LanguageExt;

namespace ErsatzTV.Core.Interfaces.Scheduling;

public interface IPlayoutCalendarEvaluator
{
    bool IsPlayoutActive(Playout playout, DateTimeOffset currentTime);
    PlayoutRuntimeStatus GetPlayoutStatus(Playout playout, DateTimeOffset currentTime);
    Option<Playout> SelectActivePlayout(IEnumerable<Playout> channelPlayouts, DateTimeOffset currentTime);
}
