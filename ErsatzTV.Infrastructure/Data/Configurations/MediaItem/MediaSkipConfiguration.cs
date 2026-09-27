using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class MediaSkipConfiguration : IEntityTypeConfiguration<MediaSkip>
{
    public void Configure(EntityTypeBuilder<MediaSkip> builder) => builder.ToTable("MediaSkip");
}
