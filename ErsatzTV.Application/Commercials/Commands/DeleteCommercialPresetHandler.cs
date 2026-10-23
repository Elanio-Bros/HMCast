using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.Commercials;

public class DeleteCommercialPresetHandler : IRequestHandler<DeleteCommercialPreset>
{
    private readonly IDbContextFactory<TvContext> _dbContextFactory;

    public DeleteCommercialPresetHandler(IDbContextFactory<TvContext> dbContextFactory)
    {
        _dbContextFactory = dbContextFactory;
    }

    public async Task Handle(DeleteCommercialPreset request, CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await _dbContextFactory.CreateDbContextAsync(cancellationToken);
        var preset = await dbContext.CommercialPresets.FirstOrDefaultAsync(p => p.Id == request.Id, cancellationToken);
        if (preset is not null)
        {
            dbContext.CommercialPresets.Remove(preset);
            await dbContext.SaveChangesAsync(cancellationToken);
        }
    }
}
