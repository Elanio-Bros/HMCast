using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class ExternalCollectionConfiguration : IEntityTypeConfiguration<ExternalCollection>
{
    public void Configure(EntityTypeBuilder<ExternalCollection> builder)
    {
        builder.ToTable("ExternalCollection");

        builder.HasOne(e => e.Collection)
            .WithMany()
            .HasForeignKey(e => e.CollectionId)
            .OnDelete(DeleteBehavior.SetNull);
    }
}
