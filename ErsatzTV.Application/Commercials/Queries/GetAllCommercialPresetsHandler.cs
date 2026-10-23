using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.Commercials;

public class GetAllCommercialPresetsHandler : IRequestHandler<GetAllCommercialPresets, List<CommercialPresetViewModel>>
{
    private readonly IDbContextFactory<TvContext> _dbContextFactory;

    public GetAllCommercialPresetsHandler(IDbContextFactory<TvContext> dbContextFactory)
    {
        _dbContextFactory = dbContextFactory;
    }

    public async Task<List<CommercialPresetViewModel>> Handle(
        GetAllCommercialPresets request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await _dbContextFactory.CreateDbContextAsync(cancellationToken);

        var presets = await dbContext.CommercialPresets
            .AsNoTracking()
            .Include(c => c.Collection)
            .Include(c => c.MediaItem)
            .ToListAsync(cancellationToken);

        return presets.Select(p => new CommercialPresetViewModel(
            p.Id,
            p.Name,
            p.Kind,
            p.CollectionId,
            p.Collection?.Name,
            p.MediaItemId,
            p.MediaItem?.Id.ToString(CultureInfo.InvariantCulture),
            p.TargetDuration,
            p.PadSeconds,
            p.StrictDuration,
            p.PlaybackOrder)).ToList();
    }
}
