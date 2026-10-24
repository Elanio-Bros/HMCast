using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.ScreenLayouts.Commands;

public record DeleteScreenLayout(int Id) : IRequest<Either<BaseError, Unit>>;

public class DeleteScreenLayoutHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<DeleteScreenLayout, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(
        DeleteScreenLayout request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        ScreenLayout layout = await dbContext.ScreenLayouts
            .Include(l => l.Elements)
            .Include(l => l.Rules)
            .FirstOrDefaultAsync(l => l.Id == request.Id, cancellationToken);

        if (layout != null)
        {
            dbContext.ScreenLayouts.Remove(layout);
            await dbContext.SaveChangesAsync(cancellationToken);
        }

        return Unit.Default;
    }
}
