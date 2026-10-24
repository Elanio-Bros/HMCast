using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class ScreenLayoutConfiguration : IEntityTypeConfiguration<ScreenLayout>
{
    public void Configure(EntityTypeBuilder<ScreenLayout> builder)
    {
        builder.ToTable("ScreenLayout");

        builder.Property(l => l.AspectRatio)
            .HasMaxLength(10)
            .HasDefaultValue("16:9");

        builder.HasMany(l => l.Elements)
            .WithOne(e => e.ScreenLayout)
            .HasForeignKey(e => e.ScreenLayoutId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasMany(l => l.Rules)
            .WithOne(r => r.ScreenLayout)
            .HasForeignKey(r => r.ScreenLayoutId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
