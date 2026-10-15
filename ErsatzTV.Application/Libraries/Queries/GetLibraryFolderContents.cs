namespace ErsatzTV.Application.Libraries;

public record GetLibraryFolderContents(int LibraryId, int? FolderId)
    : IRequest<LibraryFolderContentsViewModel>;
