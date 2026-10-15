using ErsatzTV.Core;

namespace ErsatzTV.Application.Search;

public record ValidateSearchQuery(string Query) : IRequest<Either<BaseError, int>>;
