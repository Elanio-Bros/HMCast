using ErsatzTV.Application.MediaCards;
using ErsatzTV.Core.Domain;

namespace ErsatzTV.Application.Libraries;

public record LibraryFolderBreadcrumbViewModel(int? Id, string Name);

public record LibrarySubFolderViewModel(
    int Id,
    string Name,
    string Path,
    int DirectItemCount,
    int TotalItemCount,
    int SubFolderCount,
    System.Collections.Generic.HashSet<int> MediaItemIds);

public record LibraryFolderContentsViewModel(
    int LibraryId,
    string LibraryName,
    LibraryMediaKind MediaKind,
    int? CurrentFolderId,
    string CurrentFolderName,
    string CurrentFolderPath,
    int? ParentFolderId,
    List<LibraryFolderBreadcrumbViewModel> Breadcrumbs,
    List<LibrarySubFolderViewModel> SubFolders,
    List<MediaCardViewModel> Items,
    int TotalItemsInLibrary);
