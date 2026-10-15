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

public class UpdateSingleMediaSkipHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdateSingleMediaSkip, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(UpdateSingleMediaSkip request, CancellationToken cancellationToken)
    {
        if (request.End <= request.Start)
        {
            return BaseError.New("End time must be greater than start time.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        MediaSkip skip = await dbContext.MediaSkips
            .FirstOrDefaultAsync(ms => ms.Id == request.MediaSkipId, cancellationToken);

        if (skip == null)
        {
            return BaseError.New($"MediaSkip with ID {request.MediaSkipId} was not found.");
        }

        skip.Start = request.Start;
        skip.End = request.End;
        skip.Kind = request.Kind;
        skip.Source = MediaSkipSource.Manual;

        await dbContext.SaveChangesAsync(cancellationToken);

        return Unit.Default;
    }
}
