using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;
using System.Threading;
using System.Threading.Tasks;

namespace ErsatzTV.Application.MediaItems;

public class RemoveMediaSkipHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<RemoveMediaSkip, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(RemoveMediaSkip request, CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        MediaSkip skip = await dbContext.MediaSkips
            .FirstOrDefaultAsync(ms => ms.Id == request.MediaSkipId, cancellationToken);

        if (skip != null)
        {
            dbContext.MediaSkips.Remove(skip);
            await dbContext.SaveChangesAsync(cancellationToken);
        }

        return Unit.Default;
    }
}
