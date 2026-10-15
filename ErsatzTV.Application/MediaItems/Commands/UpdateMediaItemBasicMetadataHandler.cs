using ErsatzTV.Core;
using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Errors;
using ErsatzTV.Infrastructure.Data;
using LanguageExt;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace ErsatzTV.Application.MediaItems;

public class UpdateMediaItemBasicMetadataHandler(IDbContextFactory<TvContext> dbContextFactory)
    : IRequestHandler<UpdateMediaItemBasicMetadata, Either<BaseError, Unit>>
{
    public async Task<Either<BaseError, Unit>> Handle(UpdateMediaItemBasicMetadata request, CancellationToken cancellationToken)
    {
        await using TvContext dbContext = await dbContextFactory.CreateDbContextAsync(cancellationToken);

        // Try Movie
        var movieMeta = await dbContext.MovieMetadata.FirstOrDefaultAsync(m => m.MovieId == request.MediaItemId, cancellationToken);
        if (movieMeta != null)
        {
            movieMeta.Title = request.Title ?? movieMeta.Title;
            movieMeta.SortTitle = request.SortTitle ?? movieMeta.SortTitle;
            movieMeta.OriginalTitle = request.OriginalTitle ?? movieMeta.OriginalTitle;
            movieMeta.Year = request.Year ?? movieMeta.Year;
            movieMeta.ContentRating = request.ContentRating ?? movieMeta.ContentRating;
            movieMeta.Plot = request.Plot ?? movieMeta.Plot;
            movieMeta.DateUpdated = DateTime.UtcNow;
            await dbContext.SaveChangesAsync(cancellationToken);
            return Unit.Default;
        }

        // Try Episode
        var episodeMeta = await dbContext.EpisodeMetadata.FirstOrDefaultAsync(e => e.EpisodeId == request.MediaItemId, cancellationToken);
        if (episodeMeta != null)
        {
            episodeMeta.Title = request.Title ?? episodeMeta.Title;
            episodeMeta.SortTitle = request.SortTitle ?? episodeMeta.SortTitle;
            episodeMeta.OriginalTitle = request.OriginalTitle ?? episodeMeta.OriginalTitle;
            episodeMeta.Year = request.Year ?? episodeMeta.Year;
            episodeMeta.Plot = request.Plot ?? episodeMeta.Plot;
            episodeMeta.DateUpdated = DateTime.UtcNow;
            await dbContext.SaveChangesAsync(cancellationToken);
            return Unit.Default;
        }

        // Try Show
        var showMeta = await dbContext.ShowMetadata.FirstOrDefaultAsync(s => s.ShowId == request.MediaItemId, cancellationToken);
        if (showMeta != null)
        {
            showMeta.Title = request.Title ?? showMeta.Title;
            showMeta.SortTitle = request.SortTitle ?? showMeta.SortTitle;
            showMeta.OriginalTitle = request.OriginalTitle ?? showMeta.OriginalTitle;
            showMeta.Year = request.Year ?? showMeta.Year;
            showMeta.ContentRating = request.ContentRating ?? showMeta.ContentRating;
            showMeta.Plot = request.Plot ?? showMeta.Plot;
            showMeta.DateUpdated = DateTime.UtcNow;
            await dbContext.SaveChangesAsync(cancellationToken);
            return Unit.Default;
        }

        // Try OtherVideo
        var otherMeta = await dbContext.OtherVideoMetadata.FirstOrDefaultAsync(ov => ov.OtherVideoId == request.MediaItemId, cancellationToken);
        if (otherMeta != null)
        {
            otherMeta.Title = request.Title ?? otherMeta.Title;
            otherMeta.SortTitle = request.SortTitle ?? otherMeta.SortTitle;
            otherMeta.OriginalTitle = request.OriginalTitle ?? otherMeta.OriginalTitle;
            otherMeta.Year = request.Year ?? otherMeta.Year;
            otherMeta.ContentRating = request.ContentRating ?? otherMeta.ContentRating;
            otherMeta.Plot = request.Plot ?? otherMeta.Plot;
            otherMeta.DateUpdated = DateTime.UtcNow;
            await dbContext.SaveChangesAsync(cancellationToken);
            return Unit.Default;
        }

        // Try MusicVideo
        var musicVideoMeta = await dbContext.MusicVideoMetadata.FirstOrDefaultAsync(mv => mv.MusicVideoId == request.MediaItemId, cancellationToken);
        if (musicVideoMeta != null)
        {
            musicVideoMeta.Title = request.Title ?? musicVideoMeta.Title;
            musicVideoMeta.SortTitle = request.SortTitle ?? musicVideoMeta.SortTitle;
            musicVideoMeta.OriginalTitle = request.OriginalTitle ?? musicVideoMeta.OriginalTitle;
            musicVideoMeta.Year = request.Year ?? musicVideoMeta.Year;
            musicVideoMeta.Plot = request.Plot ?? musicVideoMeta.Plot;
            musicVideoMeta.DateUpdated = DateTime.UtcNow;
            await dbContext.SaveChangesAsync(cancellationToken);
            return Unit.Default;
        }

        // Try Song
        var songMeta = await dbContext.SongMetadata.FirstOrDefaultAsync(s => s.SongId == request.MediaItemId, cancellationToken);
        if (songMeta != null)
        {
            songMeta.Title = request.Title ?? songMeta.Title;
            songMeta.SortTitle = request.SortTitle ?? songMeta.SortTitle;
            songMeta.OriginalTitle = request.OriginalTitle ?? songMeta.OriginalTitle;
            songMeta.Year = request.Year ?? songMeta.Year;
            songMeta.DateUpdated = DateTime.UtcNow;
            await dbContext.SaveChangesAsync(cancellationToken);
            return Unit.Default;
        }

        return BaseError.New($"Nenhum metadado encontrado para MediaItemId {request.MediaItemId}");
    }
}
