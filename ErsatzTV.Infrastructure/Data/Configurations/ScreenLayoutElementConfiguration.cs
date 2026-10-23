using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class ScreenLayoutElementConfiguration : IEntityTypeConfiguration<ScreenLayoutElement>
{
    public void Configure(EntityTypeBuilder<ScreenLayoutElement> builder)
    {
        builder.ToTable("ScreenLayoutElement");

        builder.HasOne(e => e.ParentElement)
            .WithMany(e => e.ChildElements)
            .HasForeignKey(e => e.ParentElementId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
