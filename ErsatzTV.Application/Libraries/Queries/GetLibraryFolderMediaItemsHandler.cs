using ErsatzTV.Application.MediaCards;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.Libraries;

public class GetLibraryFolderMediaItemsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<GetLibraryFolderMediaItems, List<MediaCardViewModel>>
{
    public async Task<List<MediaCardViewModel>> Handle(
        GetLibraryFolderMediaItems request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        Library library = await dbContext.Libraries
            .AsNoTracking()
            .Include(l => l.Paths)
            .FirstOrDefaultAsync(l => l.Id == request.LibraryId, cancellationToken);

        if (library == null)
        {
            return [];
        }

        var libraryPathIds = library.Paths.Select(p => p.Id).ToList();

        List<LibraryFolder> allFolders = await dbContext.LibraryFolders
            .AsNoTracking()
            .Where(f => libraryPathIds.Contains(f.LibraryPathId))
            .ToListAsync(cancellationToken);

        // Collect request.FolderId and all descendant folder IDs
        var targetFolderIds = new System.Collections.Generic.HashSet<int> { request.FolderId };
        var queue = new Queue<int>();
        queue.Enqueue(request.FolderId);
        while (queue.Count > 0)
        {
            int current = queue.Dequeue();
            foreach (var child in allFolders.Where(f => f.ParentId == current))
            {
                if (targetFolderIds.Add(child.Id))
                {
                    queue.Enqueue(child.Id);
                }
            }
        }

        return await GetLibraryFolderContentsHandler.LoadMediaItemsForFolders(
            dbContext,
            library.MediaKind,
            targetFolderIds,
            cancellationToken);
    }
}
