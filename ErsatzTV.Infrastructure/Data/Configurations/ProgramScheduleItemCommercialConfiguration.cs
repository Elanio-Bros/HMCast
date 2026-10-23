using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class ProgramScheduleItemCommercialConfiguration : IEntityTypeConfiguration<ProgramScheduleItemCommercial>
{
    public void Configure(EntityTypeBuilder<ProgramScheduleItemCommercial> builder)
    {
        builder.ToTable("ProgramScheduleItemCommercial");

        builder.HasOne(c => c.ProgramScheduleItem)
            .WithMany(i => i.Commercials)
            .HasForeignKey(c => c.ProgramScheduleItemId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(c => c.CommercialPreset)
            .WithMany()
            .HasForeignKey(c => c.CommercialPresetId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
