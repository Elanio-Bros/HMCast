using System;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.Commercials;

public record UpdateCommercialPreset(
    int Id,
    string Name,
    CommercialKind Kind,
    int? CollectionId,
    int? MediaItemId,
    TimeSpan? TargetDuration,
    int? PadSeconds,
    bool StrictDuration,
    PlaybackOrder PlaybackOrder) : IRequest<Either<BaseError, CommercialPresetViewModel>>;

public class UpdateCommercialPresetHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdateCommercialPreset, Either<BaseError, CommercialPresetViewModel>>
{
    public async Task<Either<BaseError, CommercialPresetViewModel>> Handle(
        UpdateCommercialPreset request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BaseError.New("O nome do comercial/vinheta é obrigatório.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        CommercialPreset preset = await dbContext.CommercialPresets
            .FirstOrDefaultAsync(p => p.Id == request.Id, cancellationToken);

        if (preset == null)
        {
            return BaseError.New($"Comercial com ID {request.Id} não foi encontrado.");
        }

        preset.Name = request.Name.Trim();
        preset.Kind = request.Kind;
        preset.CollectionId = request.CollectionId;
        preset.MediaItemId = request.MediaItemId;
        preset.TargetDuration = request.TargetDuration;
        preset.PadSeconds = request.PadSeconds;
        preset.StrictDuration = request.StrictDuration;
        preset.PlaybackOrder = request.PlaybackOrder;

        await dbContext.SaveChangesAsync(cancellationToken);

        string collectionName = null;
        if (preset.CollectionId.HasValue)
        {
            collectionName = await dbContext.Collections
                .Where(c => c.Id == preset.CollectionId.Value)
                .Select(c => c.Name)
                .FirstOrDefaultAsync(cancellationToken);
        }

        return new CommercialPresetViewModel(
            preset.Id,
            preset.Name,
            preset.Kind,
            preset.CollectionId,
            collectionName,
            preset.MediaItemId,
            preset.MediaItemId?.ToString(System.Globalization.CultureInfo.InvariantCulture),
            preset.TargetDuration,
            preset.PadSeconds,
            preset.StrictDuration,
            preset.PlaybackOrder);
    }
}
