using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.ScreenLayouts.Commands;

public class ScreenLayoutElementDto
{
    public int Id { get; set; }
    public string Name { get; set; }
    public ScreenLayoutElementType ElementType { get; set; }
    public int ZIndex { get; set; }
    public double X { get; set; }
    public double Y { get; set; }
    public double Width { get; set; }
    public double Height { get; set; }
    public double Opacity { get; set; } = 1.0;
    public string ContentPath { get; set; }
    public string TextContent { get; set; }
    public int FadeInMs { get; set; }
    public int FadeOutMs { get; set; }
}

public class ScreenLayoutRuleDto
{
    public int Id { get; set; }
    public int ElementId { get; set; }
    public ScreenLayoutRuleTrigger Trigger { get; set; }
    public ScreenLayoutRuleAction Action { get; set; }
    public int OffsetSeconds { get; set; }
    public int DurationSeconds { get; set; }
}

public record SaveScreenLayout(
    int Id,
    string Name,
    List<ScreenLayoutElementDto> Elements,
    List<ScreenLayoutRuleDto> Rules) : IRequest<Either<BaseError, int>>;

public class SaveScreenLayoutHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<SaveScreenLayout, Either<BaseError, int>>
{
    public async Task<Either<BaseError, int>> Handle(
        SaveScreenLayout request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return BaseError.New("O nome do Screen Layout é obrigatório.");
        }

        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        ScreenLayout layout;
        if (request.Id == 0)
        {
            layout = new ScreenLayout
            {
                Name = request.Name.Trim(),
                Elements = new List<ScreenLayoutElement>(),
                Rules = new List<ScreenLayoutRule>()
            };
            await dbContext.ScreenLayouts.AddAsync(layout, cancellationToken);
        }
        else
        {
            layout = await dbContext.ScreenLayouts
                .Include(l => l.Elements)
                .Include(l => l.Rules)
                .FirstOrDefaultAsync(l => l.Id == request.Id, cancellationToken);

            if (layout == null)
            {
                return BaseError.New($"Screen Layout com ID {request.Id} não encontrado.");
            }

            layout.Name = request.Name.Trim();
            layout.Elements.Clear();
            layout.Rules.Clear();
        }

        foreach (var elDto in request.Elements ?? new List<ScreenLayoutElementDto>())
        {
            layout.Elements.Add(new ScreenLayoutElement
            {
                Name = elDto.Name,
                ElementType = elDto.ElementType,
                ZIndex = elDto.ZIndex,
                X = elDto.X,
                Y = elDto.Y,
                Width = elDto.Width,
                Height = elDto.Height,
                Opacity = elDto.Opacity,
                ContentPath = elDto.ContentPath,
                TextContent = elDto.TextContent,
                FadeInMs = elDto.FadeInMs,
                FadeOutMs = elDto.FadeOutMs
            });
        }

        foreach (var ruleDto in request.Rules ?? new List<ScreenLayoutRuleDto>())
        {
            layout.Rules.Add(new ScreenLayoutRule
            {
                Trigger = ruleDto.Trigger,
                Action = ruleDto.Action,
                OffsetSeconds = ruleDto.OffsetSeconds,
                DurationSeconds = ruleDto.DurationSeconds
            });
        }

        await dbContext.SaveChangesAsync(cancellationToken);

        return layout.Id;
    }
}
