using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class ChannelFallbackSlateConfiguration : IEntityTypeConfiguration<ChannelFallbackSlate>
{
    public void Configure(EntityTypeBuilder<ChannelFallbackSlate> builder)
    {
        builder.ToTable("ChannelFallbackSlate");

        builder.HasOne(f => f.Channel)
            .WithOne(c => c.FallbackSlate)
            .HasForeignKey<ChannelFallbackSlate>(f => f.ChannelId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(f => f.MediaItem)
            .WithMany()
            .HasForeignKey(f => f.MediaItemId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne(f => f.Collection)
            .WithMany()
            .HasForeignKey(f => f.CollectionId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne(f => f.Playlist)
            .WithMany()
            .HasForeignKey(f => f.PlaylistId)
            .OnDelete(DeleteBehavior.SetNull);
    }
}
