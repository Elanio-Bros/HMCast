using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Application.ScreenLayouts.Commands;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.ScreenLayouts.Queries;

public class ScreenLayoutDetailViewModel
{
    public int Id { get; set; }
    public string Name { get; set; }
    public List<ScreenLayoutElementDto> Elements { get; set; } = [];
    public List<ScreenLayoutRuleDto> Rules { get; set; } = [];
}

public record GetScreenLayoutsWithDetails : IRequest<List<ScreenLayoutDetailViewModel>>;

public class GetScreenLayoutsWithDetailsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetScreenLayoutsWithDetails, List<ScreenLayoutDetailViewModel>>
{
    public async Task<List<ScreenLayoutDetailViewModel>> Handle(
        GetScreenLayoutsWithDetails request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        var layouts = await dbContext.ScreenLayouts
            .AsNoTracking()
            .Include(l => l.Elements)
            .Include(l => l.Rules)
            .OrderBy(l => l.Name)
            .ToListAsync(cancellationToken);

        return layouts.Select(l => new ScreenLayoutDetailViewModel
        {
            Id = l.Id,
            Name = l.Name,
            Elements = l.Elements.Select(e => new ScreenLayoutElementDto
            {
                Id = e.Id,
                Name = e.Name,
                ElementType = e.ElementType,
                ZIndex = e.ZIndex,
                X = e.X,
                Y = e.Y,
                Width = e.Width,
                Height = e.Height,
                Opacity = e.Opacity,
                ContentPath = e.ContentPath,
                TextContent = e.TextContent,
                FadeInMs = e.FadeInMs,
                FadeOutMs = e.FadeOutMs
            }).ToList(),
            Rules = l.Rules.Select(r => new ScreenLayoutRuleDto
            {
                Id = r.Id,
                ElementId = r.ElementId,
                Trigger = r.Trigger,
                Action = r.Action,
                OffsetSeconds = r.OffsetSeconds,
                DurationSeconds = r.DurationSeconds
            }).ToList()
        }).ToList();
    }
}
