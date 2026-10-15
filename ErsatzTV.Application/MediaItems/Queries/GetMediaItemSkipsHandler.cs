using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace ErsatzTV.Application.MediaItems;

public class GetMediaItemSkipsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetMediaItemSkips, List<MediaSkip>>
{
    public async Task<List<MediaSkip>> Handle(GetMediaItemSkips request, CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);
        
        var skips = await dbContext.MediaSkips
            .Where(ms => ms.MediaItemId == request.MediaItemId)
            .ToListAsync(cancellationToken);

        return skips.OrderBy(ms => ms.Start).ToList();
    }
}
