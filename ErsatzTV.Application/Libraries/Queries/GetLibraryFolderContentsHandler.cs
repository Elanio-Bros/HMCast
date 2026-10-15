using Dapper;
using ErsatzTV.Application.MediaCards;
using ErsatzTV.Application.Search;
using ErsatzTV.Core.Domain;
using ErsatzTV.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using static ErsatzTV.Application.MediaCards.Mapper;

namespace ErsatzTV.Application.Libraries;

public class GetLibraryFolderContentsHandler(IDbContextFactory<TvContext> dbContextFactory)
    : QuerySearchIndexHandlerBase, IRequestHandler<GetLibraryFolderContents, LibraryFolderContentsViewModel>
{
    public async Task<LibraryFolderContentsViewModel> Handle(
        GetLibraryFolderContents request,
        CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        Library library = await dbContext.Libraries
            .AsNoTracking()
            .Include(l => l.Paths)
            .FirstOrDefaultAsync(l => l.Id == request.LibraryId, cancellationToken);

        if (library == null)
        {
            return null;
        }

        var libraryPathIds = library.Paths.Select(p => p.Id).ToList();

        List<LibraryFolder> allFolders = await dbContext.LibraryFolders
            .AsNoTracking()
            .Where(f => libraryPathIds.Contains(f.LibraryPathId))
            .ToListAsync(cancellationToken);

        int totalItemsInLibrary = 0;
        try
        {
            totalItemsInLibrary = await dbContext.Connection.QuerySingleAsync<int>(
                @"SELECT COUNT(*) FROM MediaItem
                      INNER JOIN LibraryPath LP on MediaItem.LibraryPathId = LP.Id
                      WHERE LP.LibraryId = @LibraryId",
                new { request.LibraryId });
        }
        catch
        {
            // fallback if table query fails
        }

        // Direct item count per folder
        var allFolderIds = allFolders.Select(f => f.Id).ToList();
        var directCounts = new System.Collections.Generic.Dictionary<int, int>();
        var directItemsByFolder = new System.Collections.Generic.Dictionary<int, System.Collections.Generic.List<int>>();

        if (allFolderIds.Count > 0)
        {
            try
            {
                var folderPairs = await dbContext.Connection.QueryAsync<(int LibraryFolderId, int MediaItemId)>(
                    @"SELECT mf.LibraryFolderId, COALESCE(mv.OtherVideoId, mv.MovieId, mv.EpisodeId, mv.MusicVideoId, mv.SongId, mv.ImageId) AS MediaItemId
                      FROM MediaFile mf
                      INNER JOIN MediaVersion mv ON mf.MediaVersionId = mv.Id
                      WHERE mf.LibraryFolderId IN @allFolderIds",
                    new { allFolderIds });

                directItemsByFolder = folderPairs
                    .Where(p => p.MediaItemId > 0)
                    .GroupBy(p => p.LibraryFolderId)
                    .ToDictionary(g => g.Key, g => g.Select(p => p.MediaItemId).Distinct().ToList());

                directCounts = directItemsByFolder.ToDictionary(k => k.Key, v => v.Value.Count);
            }
            catch
            {
                // fallback
            }
        }

        System.Collections.Generic.HashSet<int> GetMediaItemIdsRecursive(int folderId)
        {
            var set = new System.Collections.Generic.HashSet<int>();
            if (directItemsByFolder.TryGetValue(folderId, out var direct))
            {
                foreach (var id in direct)
                {
                    set.Add(id);
                }
            }
            foreach (var child in allFolders.Where(f => f.ParentId == folderId && f.Id != folderId))
            {
                foreach (var id in GetMediaItemIdsRecursive(child.Id))
                {
                    set.Add(id);
                }
            }
            return set;
        }

        int GetTotalItemCountRecursive(int folderId)
        {
            int count = directCounts.GetValueOrDefault(folderId, 0);
            foreach (var child in allFolders.Where(f => f.ParentId == folderId && f.Id != folderId))
            {
                count += GetTotalItemCountRecursive(child.Id);
            }
            return count;
        }

        LibraryFolder currentFolder = null;
        int? currentFolderId = null;
        string currentFolderName = library.Name;
        string currentFolderPath = string.Empty;
        int? parentFolderId = null;

        var breadcrumbs = new List<LibraryFolderBreadcrumbViewModel>
        {
            new(null, library.Name)
        };

        List<LibraryFolder> subFolderEntities;

        if (request.FolderId.HasValue)
        {
            currentFolder = allFolders.FirstOrDefault(f => f.Id == request.FolderId.Value);
            if (currentFolder != null)
            {
                currentFolderId = currentFolder.Id;
                currentFolderName = GetFolderName(currentFolder.Path);
                currentFolderPath = currentFolder.Path;
                parentFolderId = currentFolder.ParentId;

                // Build breadcrumbs walking up (protect against loops)
                var ancestors = new List<LibraryFolder>();
                var visited = new System.Collections.Generic.HashSet<int> { currentFolder.Id };
                var curr = currentFolder;
                while (curr != null && curr.ParentId.HasValue && !visited.Contains(curr.ParentId.Value))
                {
                    var parent = allFolders.FirstOrDefault(f => f.Id == curr.ParentId.Value);
                    if (parent != null)
                    {
                        visited.Add(parent.Id);
                        ancestors.Insert(0, parent);
                    }
                    curr = parent;
                }

                foreach (var ancestor in ancestors)
                {
                    breadcrumbs.Add(new(ancestor.Id, GetFolderName(ancestor.Path)));
                }

                breadcrumbs.Add(new(currentFolder.Id, currentFolderName));

                subFolderEntities = allFolders.Where(f => f.ParentId == currentFolder.Id && f.Id != currentFolder.Id).OrderBy(f => f.Path).ToList();
            }
            else
            {
                subFolderEntities = [];
            }
        }
        else
        {
            // Root view
            var topFolders = allFolders.Where(f => f.ParentId == null).ToList();
            if (topFolders.Count == 1)
            {
                // Single root folder represents the library path
                var singleRoot = topFolders[0];
                currentFolderId = singleRoot.Id;
                currentFolderPath = singleRoot.Path;
                currentFolder = singleRoot;
                subFolderEntities = allFolders.Where(f => f.ParentId == singleRoot.Id && f.Id != singleRoot.Id).OrderBy(f => f.Path).ToList();
            }
            else
            {
                subFolderEntities = topFolders.OrderBy(f => f.Path).ToList();
            }
        }

        var subFolders = subFolderEntities.Select(sf => new LibrarySubFolderViewModel(
            sf.Id,
            GetFolderName(sf.Path),
            sf.Path,
            directCounts.GetValueOrDefault(sf.Id, 0),
            GetTotalItemCountRecursive(sf.Id),
            allFolders.Count(f => f.ParentId == sf.Id && f.Id != sf.Id),
            GetMediaItemIdsRecursive(sf.Id)
        )).ToList();

        // Load items for currentFolderId
        List<MediaCardViewModel> items = [];
        if (currentFolderId.HasValue)
        {
            var folderSet = new System.Collections.Generic.HashSet<int> { currentFolderId.Value };
            items = await LoadMediaItemsForFolders(dbContext, library.MediaKind, folderSet, cancellationToken);
        }

        return new LibraryFolderContentsViewModel(
            library.Id,
            library.Name,
            library.MediaKind,
            currentFolderId,
            currentFolderName,
            currentFolderPath,
            parentFolderId,
            breadcrumbs,
            subFolders,
            items,
            totalItemsInLibrary);
    }

    public static async Task<List<MediaCardViewModel>> LoadMediaItemsForFolders(
        TvContext dbContext,
        LibraryMediaKind mediaKind,
        System.Collections.Generic.HashSet<int> folderIds,
        CancellationToken cancellationToken)
    {
        Option<JellyfinMediaSource> maybeJellyfin = await GetJellyfin(dbContext, cancellationToken);
        Option<EmbyMediaSource> maybeEmby = await GetEmby(dbContext, cancellationToken);

        List<MediaCardViewModel> items = [];

        var folderList = folderIds.ToList();
        if (folderList.Count == 0)
        {
            return items;
        }

        // Query distinct media item IDs in these folders via Dapper (avoids SQLite APPLY translation error)
        var itemIds = (await dbContext.Connection.QueryAsync<int>(
            @"SELECT DISTINCT COALESCE(mv.OtherVideoId, mv.MovieId, mv.EpisodeId, mv.MusicVideoId, mv.SongId, mv.ImageId) AS MediaItemId
              FROM MediaFile mf
              INNER JOIN MediaVersion mv ON mf.MediaVersionId = mv.Id
              WHERE mf.LibraryFolderId IN @folderList",
            new { folderList })).ToList();

        if (itemIds.Count == 0)
        {
            return items;
        }

        switch (mediaKind)
        {
            case LibraryMediaKind.Movies:
            {
                var movies = await dbContext.MovieMetadata
                    .AsNoTracking()
                    .AsSplitQuery()
                    .Where(mm => itemIds.Contains(mm.MovieId))
                    .Include(mm => mm.Artwork)
                    .Include(mm => mm.Movie)
                        .ThenInclude(m => m.MediaVersions)
                        .ThenInclude(mv => mv.MediaFiles)
                    .OrderBy(mm => mm.SortTitle)
                    .ToListAsync(cancellationToken);

                items.AddRange(movies.Select(m => ProjectToViewModel(m, maybeJellyfin, maybeEmby)));
                break;
            }
            case LibraryMediaKind.Shows:
            {
                var episodes = await dbContext.EpisodeMetadata
                    .AsNoTracking()
                    .AsSplitQuery()
                    .Where(em => itemIds.Contains(em.EpisodeId))
                    .Include(em => em.Artwork)
                    .Include(em => em.Directors)
                    .Include(em => em.Writers)
                    .Include(em => em.Episode)
                        .ThenInclude(e => e.Season)
                        .ThenInclude(s => s.Show)
                        .ThenInclude(s => s.ShowMetadata)
                    .Include(em => em.Episode)
                        .ThenInclude(e => e.MediaVersions)
                        .ThenInclude(mv => mv.MediaFiles)
                    .OrderBy(em => em.Episode.Season.SeasonNumber)
                    .ThenBy(em => em.EpisodeNumber)
                    .ToListAsync(cancellationToken);

                items.AddRange(episodes.Select(e => ProjectToViewModel(e, maybeJellyfin, maybeEmby, false, string.Empty)));
                break;
            }
            case LibraryMediaKind.OtherVideos:
            {
                var otherVideos = await dbContext.OtherVideoMetadata
                    .AsNoTracking()
                    .AsSplitQuery()
                    .Where(ovm => itemIds.Contains(ovm.OtherVideoId))
                    .Include(ovm => ovm.Artwork)
                    .Include(ovm => ovm.OtherVideo)
                        .ThenInclude(ov => ov.MediaVersions)
                        .ThenInclude(mv => mv.MediaFiles)
                    .OrderBy(ovm => ovm.SortTitle)
                    .ToListAsync(cancellationToken);

                items.AddRange(otherVideos.Select(ProjectToViewModel));
                break;
            }
            case LibraryMediaKind.MusicVideos:
            {
                var musicVideos = await dbContext.MusicVideoMetadata
                    .AsNoTracking()
                    .AsSplitQuery()
                    .Where(mvm => itemIds.Contains(mvm.MusicVideoId))
                    .Include(mvm => mvm.Artwork)
                    .Include(mvm => mvm.MusicVideo)
                        .ThenInclude(mv => mv.Artist)
                        .ThenInclude(a => a.ArtistMetadata)
                    .Include(mvm => mvm.MusicVideo)
                        .ThenInclude(mv => mv.MediaVersions)
                        .ThenInclude(mv => mv.MediaFiles)
                    .OrderBy(mvm => mvm.SortTitle)
                    .ToListAsync(cancellationToken);

                items.AddRange(musicVideos.Select(mv => ProjectToViewModel(mv, string.Empty)));
                break;
            }
            case LibraryMediaKind.Songs:
            {
                var songs = await dbContext.SongMetadata
                    .AsNoTracking()
                    .AsSplitQuery()
                    .Where(sm => itemIds.Contains(sm.SongId))
                    .Include(sm => sm.Artwork)
                    .Include(sm => sm.Song)
                        .ThenInclude(s => s.MediaVersions)
                        .ThenInclude(mv => mv.MediaFiles)
                    .OrderBy(sm => sm.SortTitle)
                    .ToListAsync(cancellationToken);

                items.AddRange(songs.Select(ProjectToViewModel));
                break;
            }
            case LibraryMediaKind.Images:
            {
                var images = await dbContext.ImageMetadata
                    .AsNoTracking()
                    .AsSplitQuery()
                    .Where(im => itemIds.Contains(im.ImageId))
                    .Include(im => im.Artwork)
                    .Include(im => im.Image)
                        .ThenInclude(i => i.MediaVersions)
                        .ThenInclude(mv => mv.MediaFiles)
                    .OrderBy(im => im.SortTitle)
                    .ToListAsync(cancellationToken);

                items.AddRange(images.Select(ProjectToViewModel));
                break;
            }
        }

        return items;
    }

    private static string GetFolderName(string path)
    {
        if (string.IsNullOrWhiteSpace(path)) return string.Empty;
        string trimmed = path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        string name = Path.GetFileName(trimmed);
        return string.IsNullOrWhiteSpace(name) ? path : name;
    }
}
