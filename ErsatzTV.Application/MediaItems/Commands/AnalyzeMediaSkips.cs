using ErsatzTV.Core;

namespace ErsatzTV.Application.MediaItems;

public record AnalyzeMediaSkips(int MediaItemId) : IRequest<Either<BaseError, Unit>>, IBackgroundServiceRequest;
