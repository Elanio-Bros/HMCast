using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ErsatzTV.Infrastructure.Sqlite.Migrations
{
    /// <inheritdoc />
    public partial class Add_ShowCut_Remove_IsRadioMode : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {


            migrationBuilder.AddColumn<bool>(
                name: "ShowCut",
                table: "MediaItem",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowFinish",
                table: "MediaItem",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowIntro",
                table: "MediaItem",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowPreview",
                table: "MediaItem",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowRecap",
                table: "MediaItem",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.CreateTable(
                name: "MediaSkip",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    MediaItemId = table.Column<int>(type: "INTEGER", nullable: false),
                    Start = table.Column<TimeSpan>(type: "TEXT", nullable: false),
                    End = table.Column<TimeSpan>(type: "TEXT", nullable: false),
                    Kind = table.Column<int>(type: "INTEGER", nullable: false),
                    Source = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_MediaSkip", x => x.Id);
                    table.ForeignKey(
                        name: "FK_MediaSkip_MediaItem_MediaItemId",
                        column: x => x.MediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_MediaSkip_MediaItemId",
                table: "MediaSkip",
                column: "MediaItemId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "MediaSkip");



            migrationBuilder.DropColumn(
                name: "ShowCut",
                table: "MediaItem");

            migrationBuilder.DropColumn(
                name: "ShowFinish",
                table: "MediaItem");

            migrationBuilder.DropColumn(
                name: "ShowIntro",
                table: "MediaItem");

            migrationBuilder.DropColumn(
                name: "ShowPreview",
                table: "MediaItem");

            migrationBuilder.DropColumn(
                name: "ShowRecap",
                table: "MediaItem");


        }
    }
}
