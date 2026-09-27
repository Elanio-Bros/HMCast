using System.Globalization;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class DateTimeOffsetCollectionValueConverter : ValueConverter<ICollection<DateTimeOffset>, string>
{
    private const string Format = "o"; // ISO 8601 round-trip format

    public DateTimeOffsetCollectionValueConverter() : base(
        i => string.Join(",", i.Select(d => d.ToString(Format, CultureInfo.InvariantCulture))),
        s => string.IsNullOrWhiteSpace(s)
            ? Array.Empty<DateTimeOffset>()
            : s.Split(',', StringSplitOptions.None)
                .Select(v => DateTimeOffset.ParseExact(v, Format, CultureInfo.InvariantCulture))
                .ToArray())
    {
    }
}
