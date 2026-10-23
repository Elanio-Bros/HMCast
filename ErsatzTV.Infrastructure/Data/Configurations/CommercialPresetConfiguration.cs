using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class CommercialPresetConfiguration : IEntityTypeConfiguration<CommercialPreset>
{
    public void Configure(EntityTypeBuilder<CommercialPreset> builder)
    {
        builder.ToTable("CommercialPreset");

        builder.HasOne(c => c.Collection)
            .WithMany()
            .HasForeignKey(c => c.CollectionId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne(c => c.MediaItem)
            .WithMany()
            .HasForeignKey(c => c.MediaItemId)
            .OnDelete(DeleteBehavior.SetNull);
    }
}
