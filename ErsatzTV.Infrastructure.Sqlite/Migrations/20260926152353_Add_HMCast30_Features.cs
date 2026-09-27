using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ErsatzTV.Infrastructure.Sqlite.Migrations
{
    /// <inheritdoc />
    public partial class Add_HMCast30_Features : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "IsRadioMode",
                table: "Channel");

            migrationBuilder.AddColumn<int>(
                name: "Mode",
                table: "Channel",
                type: "INTEGER",
                nullable: false,
                defaultValue: 0);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Mode",
                table: "Channel");

            migrationBuilder.AddColumn<bool>(
                name: "IsRadioMode",
                table: "Channel",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);
        }
    }
}
