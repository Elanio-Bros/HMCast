using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class ScreenLayoutRuleConfiguration : IEntityTypeConfiguration<ScreenLayoutRule>
{
    public void Configure(EntityTypeBuilder<ScreenLayoutRule> builder)
    {
        builder.ToTable("ScreenLayoutRule");

        builder.HasOne(r => r.Element)
            .WithMany()
            .HasForeignKey(r => r.ElementId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
