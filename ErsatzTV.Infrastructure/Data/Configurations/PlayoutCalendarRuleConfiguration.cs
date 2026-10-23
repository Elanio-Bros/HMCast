using ErsatzTV.Core.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ErsatzTV.Infrastructure.Data.Configurations;

public class PlayoutCalendarRuleConfiguration : IEntityTypeConfiguration<PlayoutCalendarRule>
{
    public void Configure(EntityTypeBuilder<PlayoutCalendarRule> builder)
    {
        builder.ToTable("PlayoutCalendarRule");

        builder.HasOne(r => r.Playout)
            .WithMany(p => p.CalendarRules)
            .HasForeignKey(r => r.PlayoutId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
