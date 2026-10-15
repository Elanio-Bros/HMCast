using ErsatzTV.Core;
using ErsatzTV.Core.Errors;
using ErsatzTV.Core.Interfaces.Search;

namespace ErsatzTV.Application.Search;

public class ValidateSearchQueryHandler(ISearchIndex searchIndex)
    : IRequestHandler<ValidateSearchQuery, Either<BaseError, int>>
{
    public async Task<Either<BaseError, int>> Handle(
        ValidateSearchQuery request,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Query))
        {
            return 0;
        }

        string query = request.Query.Trim();

        // 1. Check unbalanced quotes
        int quoteCount = query.Count(c => c == '"');
        if (quoteCount % 2 != 0)
        {
            return BaseError.New("Unclosed double quote (\") detected.");
        }

        // 2. Check unbalanced parentheses
        int openParen = query.Count(c => c == '(');
        int closeParen = query.Count(c => c == ')');
        if (openParen != closeParen)
        {
            return BaseError.New($"Unbalanced parentheses: {openParen} '(' vs {closeParen} ')'.");
        }

        // 3. Check unbalanced square brackets
        int openBracket = query.Count(c => c == '[');
        int closeBracket = query.Count(c => c == ']');
        if (openBracket != closeBracket)
        {
            return BaseError.New("Unbalanced square brackets '[' and ']'.");
        }

        // 4. Check trailing logical operators
        if (query.EndsWith(" AND", StringComparison.OrdinalIgnoreCase) ||
            query.EndsWith(" OR", StringComparison.OrdinalIgnoreCase) ||
            query.EndsWith(" NOT", StringComparison.OrdinalIgnoreCase) ||
            query.Equals("AND", StringComparison.OrdinalIgnoreCase) ||
            query.Equals("OR", StringComparison.OrdinalIgnoreCase) ||
            query.Equals("NOT", StringComparison.OrdinalIgnoreCase))
        {
            return BaseError.New("Query ends with an incomplete operator (AND / OR / NOT).");
        }

        try
        {
            var result = await searchIndex.Search(query, string.Empty, 0, 1, cancellationToken);
            return result.TotalCount;
        }
        catch (Exception ex)
        {
            return BaseError.New($"Query execution error: {ex.Message}");
        }
    }
}
