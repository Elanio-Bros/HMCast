using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace ErsatzTV.Application.MediaItems;

public class RemoveMediaSkipsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<RemoveMediaSkips, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(RemoveMediaSkips request, CancellationToken cancellationToken)
    {
        if (request.MediaSkipIds == null || request.MediaSkipIds.Count == 0)
        {
            return Unit.Default;
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        var skips = await dbContext.MediaSkips
            .Where(ms => request.MediaSkipIds.Contains(ms.Id))
            .ToListAsync(cancellationToken);

        if (skips.Count != 0)
        {
            dbContext.MediaSkips.RemoveRange(skips);
            await dbContext.SaveChangesAsync(cancellationToken);
        }

        return Unit.Default;
    }
}
