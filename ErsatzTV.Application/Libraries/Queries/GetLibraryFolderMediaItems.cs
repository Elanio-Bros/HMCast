using ErsatzTV.Application.MediaCards;

namespace ErsatzTV.Application.Libraries;

public record GetLibraryFolderMediaItems(int LibraryId, int FolderId)
    : IRequest<List<MediaCardViewModel>>;
