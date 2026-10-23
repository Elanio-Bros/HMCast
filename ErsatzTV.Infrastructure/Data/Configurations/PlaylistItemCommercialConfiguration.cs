using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class PlaylistItemCommercialConfiguration : IEntityTypeConfiguration<PlaylistItemCommercial>
{
    public void Configure(EntityTypeBuilder<PlaylistItemCommercial> builder)
    {
        builder.ToTable("PlaylistItemCommercial");

        builder.HasOne(c => c.PlaylistItem)
            .WithMany(i => i.Commercials)
            .HasForeignKey(c => c.PlaylistItemId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(c => c.CommercialPreset)
            .WithMany()
            .HasForeignKey(c => c.CommercialPresetId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
