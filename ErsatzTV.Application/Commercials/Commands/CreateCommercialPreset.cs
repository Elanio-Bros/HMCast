using System;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.Commercials;

public record CreateCommercialPreset(
    string Name,
    CommercialKind Kind,
    int? CollectionId,
    int? MediaItemId,
    TimeSpan? TargetDuration,
    int? PadSeconds,
    bool StrictDuration,
    PlaybackOrder PlaybackOrder) : IRequest<Either<BaseError, CommercialPresetViewModel>>;

public class CreateCommercialPresetHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<CreateCommercialPreset, Either<BaseError, CommercialPresetViewModel>>
{
    public async Task<Either<BaseError, CommercialPresetViewModel>> Handle(
        CreateCommercialPreset request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BaseError.New("O nome do comercial/vinheta é obrigatório.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        var preset = new CommercialPreset
        {
            Name = request.Name.Trim(),
            Kind = request.Kind,
            CollectionId = request.CollectionId,
            MediaItemId = request.MediaItemId,
            TargetDuration = request.TargetDuration,
            PadSeconds = request.PadSeconds,
            StrictDuration = request.StrictDuration,
            PlaybackOrder = request.PlaybackOrder
        };

        await dbContext.CommercialPresets.AddAsync(preset, cancellationToken);
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
