using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.ScreenLayouts.Queries;

public record ScreenLayoutViewModel(int Id, string Name);

public record GetAllScreenLayouts : IRequest<List<ScreenLayoutViewModel>>;

public class GetAllScreenLayoutsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetAllScreenLayouts, List<ScreenLayoutViewModel>>
{
    public async Task<List<ScreenLayoutViewModel>> Handle(GetAllScreenLayouts request, CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);
        return await dbContext.ScreenLayouts
            .AsNoTracking()
            .OrderBy(l => l.Name)
            .Select(l => new ScreenLayoutViewModel(l.Id, l.Name))
            .ToListAsync(cancellationToken);
    }
}
