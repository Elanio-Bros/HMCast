using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Core.Extensions;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace ErsatzTV.Application.MediaItems;

public class CopyMediaSkipsToItemsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<CopyMediaSkipsToItems, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(CopyMediaSkipsToItems request, CancellationToken cancellationToken)
    {
        if (request.TargetMediaItemIds == null || request.TargetMediaItemIds.Count == 0)
        {
            return BaseError.New("No target media items selected.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        // Load skips to copy
        List<MediaSkip> sourceSkips = await dbContext.MediaSkips
            .Where(ms => ms.MediaItemId == request.SourceMediaItemId && request.SelectedSkipIds.Contains(ms.Id))
            .ToListAsync(cancellationToken);

        if (sourceSkips.Count == 0)
        {
            return BaseError.New("No cutouts found to replicate.");
        }

        // Load source media item to know its duration
        MediaItem sourceItem = await dbContext.MediaItems
            .Include(mi => (mi as Movie).MediaVersions)
            .Include(mi => (mi as Episode).MediaVersions)
            .Include(mi => (mi as OtherVideo).MediaVersions)
            .Include(mi => (mi as MusicVideo).MediaVersions)
            .Include(mi => (mi as Song).MediaVersions)
            .FirstOrDefaultAsync(mi => mi.Id == request.SourceMediaItemId, cancellationToken);

        TimeSpan sourceDuration = sourceItem?.GetHeadVersion()?.Duration ?? TimeSpan.Zero;

        // Load target media items with their versions to know their exact duration
        List<MediaItem> targetItems = await dbContext.MediaItems
            .Include(mi => mi.MediaSkips)
            .Include(mi => (mi as Movie).MediaVersions)
            .Include(mi => (mi as Episode).MediaVersions)
            .Include(mi => (mi as OtherVideo).MediaVersions)
            .Include(mi => (mi as MusicVideo).MediaVersions)
            .Include(mi => (mi as Song).MediaVersions)
            .Where(mi => request.TargetMediaItemIds.Contains(mi.Id) && mi.Id != request.SourceMediaItemId)
            .ToListAsync(cancellationToken);

        foreach (MediaItem targetItem in targetItems)
        {
            TimeSpan targetDuration = targetItem.GetHeadVersion()?.Duration ?? TimeSpan.Zero;

            foreach (MediaSkip src in sourceSkips)
            {
                TimeSpan skipDuration = src.End - src.Start;
                if (skipDuration <= TimeSpan.Zero) continue;

                TimeSpan targetStart = src.Start;
                TimeSpan targetEnd = src.End;

                switch (src.Kind)
                {
                    // 1. ANCORADOS NO INÍCIO (RELATIVOS POR DURAÇÃO A PARTIR DO OFFSET)
                    case MediaSkipKind.Intro:
                    case MediaSkipKind.Recap:
                        targetStart = src.Start;
                        targetEnd = targetStart + skipDuration;

                        // Se a mídia destino for menor que o ponto de início, não aplica
                        if (targetDuration > TimeSpan.Zero && targetStart >= targetDuration)
                            continue;

                        // Se ultrapassar o final, limita na duração total
                        if (targetDuration > TimeSpan.Zero && targetEnd > targetDuration)
                            targetEnd = targetDuration;
                        break;

                    // 2. ANCORADOS NO FIM (RELATIVOS À DURAÇÃO FINAL DO DESTINO)
                    case MediaSkipKind.Finish:
                    case MediaSkipKind.Preview:
                        if (targetDuration > TimeSpan.Zero)
                        {
                            // Calcula a distância do fim da mídia de origem
                            TimeSpan offsetFromSourceEnd = sourceDuration > TimeSpan.Zero && sourceDuration >= src.End
                                ? sourceDuration - src.End
                                : TimeSpan.Zero;

                            targetEnd = targetDuration - offsetFromSourceEnd;
                            targetStart = targetEnd - skipDuration;

                            if (targetStart < TimeSpan.Zero) targetStart = TimeSpan.Zero;
                            if (targetEnd > targetDuration) targetEnd = targetDuration;
                        }
                        break;

                    // 3. CORTES INTERMEDIÁRIOS (CUT - COMERCIAIS / BLACKOUTS)
                    case MediaSkipKind.Cut:
                    default:
                        // Mantém exatamente do jeito que foi colocado originalmente
                        targetStart = src.Start;
                        targetEnd = src.End;

                        // Proteção: não insere se o início passar da duração da mídia destino
                        if (targetDuration > TimeSpan.Zero && targetStart >= targetDuration)
                            continue;

                        // Proteção: se o final ultrapassar, limita ao final da mídia
                        if (targetDuration > TimeSpan.Zero && targetEnd > targetDuration)
                            targetEnd = targetDuration;
                        break;
                }

                // Proteção contra tempos inválidos
                if (targetEnd <= targetStart)
                    continue;

                // Se já existir um skip com mesma tipagem e tempos exatos, ignora
                bool alreadyExists = targetItem.MediaSkips.Any(ms =>
                    ms.Kind == src.Kind &&
                    ms.Start == targetStart &&
                    ms.End == targetEnd);

                if (!alreadyExists)
                {
                    // Para Intro e Finish, se já existir um registrado, atualiza em vez de duplicar
                    if (src.Kind == MediaSkipKind.Intro || src.Kind == MediaSkipKind.Finish)
                    {
                        var existingSameKind = targetItem.MediaSkips.FirstOrDefault(ms => ms.Kind == src.Kind);
                        if (existingSameKind != null)
                        {
                            existingSameKind.Start = targetStart;
                            existingSameKind.End = targetEnd;
                            existingSameKind.Source = MediaSkipSource.Manual;
                            continue;
                        }
                    }

                    var newSkip = new MediaSkip
                    {
                        MediaItemId = targetItem.Id,
                        Start = targetStart,
                        End = targetEnd,
                        Kind = src.Kind,
                        Source = MediaSkipSource.Manual
                    };
                    dbContext.MediaSkips.Add(newSkip);
                    targetItem.MediaSkips.Add(newSkip);
                }
            }
        }

        await dbContext.SaveChangesAsync(cancellationToken);
        return Unit.Default;
    }
}
