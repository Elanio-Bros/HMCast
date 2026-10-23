using System;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ErsatzTV.Infrastructure.MySql.Migrations
{
    /// <inheritdoc />
    public partial class Add_HMCast30_Architecture : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Playout_Deco_DecoId",
                table: "Playout");

            migrationBuilder.DropForeignKey(
                name: "FK_PlayoutHistory_Block_BlockId",
                table: "PlayoutHistory");

            migrationBuilder.DropForeignKey(
                name: "FK_PlayoutProgramScheduleAnchor_RerunCollection_RerunCollection~",
                table: "PlayoutProgramScheduleAnchor");

            migrationBuilder.DropForeignKey(
                name: "FK_ProgramScheduleItem_RerunCollection_RerunCollectionId",
                table: "ProgramScheduleItem");

            migrationBuilder.DropTable(
                name: "BlockItemGraphicsElement");

            migrationBuilder.DropTable(
                name: "BlockItemWatermark");

            migrationBuilder.DropTable(
                name: "DecoBreakContent");

            migrationBuilder.DropTable(
                name: "DecoGraphicsElement");

            migrationBuilder.DropTable(
                name: "DecoTemplateItem");

            migrationBuilder.DropTable(
                name: "DecoWatermark");

            migrationBuilder.DropTable(
                name: "PlayoutTemplate");

            migrationBuilder.DropTable(
                name: "RerunHistory");

            migrationBuilder.DropTable(
                name: "TemplateItem");

            migrationBuilder.DropTable(
                name: "BlockItem");

            migrationBuilder.DropTable(
                name: "Deco");

            migrationBuilder.DropTable(
                name: "DecoTemplate");

            migrationBuilder.DropTable(
                name: "RerunCollection");

            migrationBuilder.DropTable(
                name: "Template");

            migrationBuilder.DropTable(
                name: "Block");

            migrationBuilder.DropTable(
                name: "DecoGroup");

            migrationBuilder.DropTable(
                name: "DecoTemplateGroup");

            migrationBuilder.DropTable(
                name: "TemplateGroup");

            migrationBuilder.DropTable(
                name: "BlockGroup");

            migrationBuilder.DropIndex(
                name: "IX_PlayoutProgramScheduleAnchor_RerunCollectionId",
                table: "PlayoutProgramScheduleAnchor");

            migrationBuilder.DropIndex(
                name: "IX_PlayoutHistory_BlockId",
                table: "PlayoutHistory");

            migrationBuilder.DropIndex(
                name: "IX_Playout_DecoId",
                table: "Playout");

            migrationBuilder.DropColumn(
                name: "Count",
                table: "ProgramScheduleMultipleItem");

            migrationBuilder.DropColumn(
                name: "RerunCollectionId",
                table: "PlayoutProgramScheduleAnchor");

            migrationBuilder.DropColumn(
                name: "BlockId",
                table: "PlayoutHistory");

            migrationBuilder.RenameColumn(
                name: "RerunCollectionId",
                table: "ProgramScheduleItem",
                newName: "ScreenLayoutId");

            migrationBuilder.RenameIndex(
                name: "IX_ProgramScheduleItem_RerunCollectionId",
                table: "ProgramScheduleItem",
                newName: "IX_ProgramScheduleItem_ScreenLayoutId");

            migrationBuilder.RenameColumn(
                name: "DecoId",
                table: "Playout",
                newName: "SourceId");

            migrationBuilder.AddColumn<int>(
                name: "DurationMode",
                table: "ProgramScheduleItem",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<bool>(
                name: "FillCommercialGapsWithFillers",
                table: "ProgramScheduleItem",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<int>(
                name: "ItemCount",
                table: "ProgramScheduleItem",
                type: "int",
                nullable: true);

            migrationBuilder.AddColumn<bool>(
                name: "RespectMediaSkipChapters",
                table: "ProgramScheduleItem",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<int>(
                name: "StartType",
                table: "ProgramScheduleItem",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<TimeSpan>(
                name: "TargetDuration",
                table: "ProgramScheduleItem",
                type: "time(6)",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "SpecificDates",
                table: "ProgramScheduleAlternate",
                type: "longtext",
                nullable: true)
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.AddColumn<int>(
                name: "CalendarMode",
                table: "Playout",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "DaysToBuild",
                table: "Playout",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "DeliveryMode",
                table: "Playout",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<bool>(
                name: "IsEnabled",
                table: "Playout",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<int>(
                name: "PlayoutMode",
                table: "Playout",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "ScreenLayoutId",
                table: "Playout",
                type: "int",
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "SourceKind",
                table: "Playout",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<bool>(
                name: "ShowCut",
                table: "MediaItem",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowFinish",
                table: "MediaItem",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowIntro",
                table: "MediaItem",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowPreview",
                table: "MediaItem",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "ShowRecap",
                table: "MediaItem",
                type: "tinyint(1)",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<int>(
                name: "OrderIndex",
                table: "CollectionItem",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "Mode",
                table: "Channel",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "ScreenLayoutId",
                table: "Channel",
                type: "int",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "ChannelFallbackSlate",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    ChannelId = table.Column<int>(type: "int", nullable: false),
                    Mode = table.Column<int>(type: "int", nullable: false),
                    MediaItemId = table.Column<int>(type: "int", nullable: true),
                    CollectionId = table.Column<int>(type: "int", nullable: true),
                    PlaylistId = table.Column<int>(type: "int", nullable: true),
                    CustomTitle = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    CustomMessage = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    IsLoop = table.Column<bool>(type: "tinyint(1)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ChannelFallbackSlate", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ChannelFallbackSlate_Channel_ChannelId",
                        column: x => x.ChannelId,
                        principalTable: "Channel",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ChannelFallbackSlate_Collection_CollectionId",
                        column: x => x.CollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_ChannelFallbackSlate_MediaItem_MediaItemId",
                        column: x => x.MediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_ChannelFallbackSlate_Playlist_PlaylistId",
                        column: x => x.PlaylistId,
                        principalTable: "Playlist",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "CommercialPreset",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Kind = table.Column<int>(type: "int", nullable: false),
                    CollectionId = table.Column<int>(type: "int", nullable: true),
                    MediaItemId = table.Column<int>(type: "int", nullable: true),
                    TargetDuration = table.Column<TimeSpan>(type: "time(6)", nullable: true),
                    PadSeconds = table.Column<int>(type: "int", nullable: true),
                    StrictDuration = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    PlaybackOrder = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CommercialPreset", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CommercialPreset_Collection_CollectionId",
                        column: x => x.CollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_CommercialPreset_MediaItem_MediaItemId",
                        column: x => x.MediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "ExternalCollection",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Description = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Provider = table.Column<int>(type: "int", nullable: false),
                    ExternalId = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Url = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    AutoSync = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    SyncFrequencyHours = table.Column<int>(type: "int", nullable: false),
                    LastSync = table.Column<DateTimeOffset>(type: "datetime(6)", nullable: true),
                    ItemCount = table.Column<int>(type: "int", nullable: false),
                    CollectionId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ExternalCollection", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ExternalCollection_Collection_CollectionId",
                        column: x => x.CollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "MediaSkip",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    MediaItemId = table.Column<int>(type: "int", nullable: false),
                    Start = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    End = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    Kind = table.Column<int>(type: "int", nullable: false),
                    Source = table.Column<int>(type: "int", nullable: false)
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
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "PlayoutCalendarRule",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PlayoutId = table.Column<int>(type: "int", nullable: false),
                    Index = table.Column<int>(type: "int", nullable: false),
                    DaysOfWeek = table.Column<int>(type: "int", nullable: false),
                    StartDate = table.Column<DateTimeOffset>(type: "datetime(6)", nullable: true),
                    EndDate = table.Column<DateTimeOffset>(type: "datetime(6)", nullable: true),
                    RecurringStartMonth = table.Column<int>(type: "int", nullable: true),
                    RecurringStartDay = table.Column<int>(type: "int", nullable: true),
                    RecurringEndMonth = table.Column<int>(type: "int", nullable: true),
                    RecurringEndDay = table.Column<int>(type: "int", nullable: true),
                    DailyStartTime = table.Column<TimeSpan>(type: "time(6)", nullable: true),
                    DailyEndTime = table.Column<TimeSpan>(type: "time(6)", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PlayoutCalendarRule", x => x.Id);
                    table.ForeignKey(
                        name: "FK_PlayoutCalendarRule_Playout_PlayoutId",
                        column: x => x.PlayoutId,
                        principalTable: "Playout",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "ScreenLayout",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ScreenLayout", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "PlaylistItemCommercial",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    PlaylistItemId = table.Column<int>(type: "int", nullable: false),
                    CommercialPresetId = table.Column<int>(type: "int", nullable: false),
                    Placement = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PlaylistItemCommercial", x => x.Id);
                    table.ForeignKey(
                        name: "FK_PlaylistItemCommercial_CommercialPreset_CommercialPresetId",
                        column: x => x.CommercialPresetId,
                        principalTable: "CommercialPreset",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_PlaylistItemCommercial_PlaylistItem_PlaylistItemId",
                        column: x => x.PlaylistItemId,
                        principalTable: "PlaylistItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "ProgramScheduleItemCommercial",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    ProgramScheduleItemId = table.Column<int>(type: "int", nullable: false),
                    CommercialPresetId = table.Column<int>(type: "int", nullable: false),
                    Placement = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProgramScheduleItemCommercial", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProgramScheduleItemCommercial_CommercialPreset_CommercialPre~",
                        column: x => x.CommercialPresetId,
                        principalTable: "CommercialPreset",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ProgramScheduleItemCommercial_ProgramScheduleItem_ProgramSch~",
                        column: x => x.ProgramScheduleItemId,
                        principalTable: "ProgramScheduleItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "ScreenLayoutElement",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    ScreenLayoutId = table.Column<int>(type: "int", nullable: false),
                    Name = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    ElementType = table.Column<int>(type: "int", nullable: false),
                    ZIndex = table.Column<int>(type: "int", nullable: false),
                    X = table.Column<double>(type: "double", nullable: false),
                    Y = table.Column<double>(type: "double", nullable: false),
                    Width = table.Column<double>(type: "double", nullable: false),
                    Height = table.Column<double>(type: "double", nullable: false),
                    Opacity = table.Column<double>(type: "double", nullable: false),
                    ContentPath = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    TextContent = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    FadeInMs = table.Column<int>(type: "int", nullable: false),
                    FadeOutMs = table.Column<int>(type: "int", nullable: false),
                    ParentElementId = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ScreenLayoutElement", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ScreenLayoutElement_ScreenLayoutElement_ParentElementId",
                        column: x => x.ParentElementId,
                        principalTable: "ScreenLayoutElement",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_ScreenLayoutElement_ScreenLayout_ScreenLayoutId",
                        column: x => x.ScreenLayoutId,
                        principalTable: "ScreenLayout",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "ScreenLayoutRule",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    ScreenLayoutId = table.Column<int>(type: "int", nullable: false),
                    ElementId = table.Column<int>(type: "int", nullable: false),
                    Trigger = table.Column<int>(type: "int", nullable: false),
                    Action = table.Column<int>(type: "int", nullable: false),
                    OffsetSeconds = table.Column<int>(type: "int", nullable: false),
                    DurationSeconds = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ScreenLayoutRule", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ScreenLayoutRule_ScreenLayoutElement_ElementId",
                        column: x => x.ElementId,
                        principalTable: "ScreenLayoutElement",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ScreenLayoutRule_ScreenLayout_ScreenLayoutId",
                        column: x => x.ScreenLayoutId,
                        principalTable: "ScreenLayout",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateIndex(
                name: "IX_Playout_ScreenLayoutId",
                table: "Playout",
                column: "ScreenLayoutId");

            migrationBuilder.CreateIndex(
                name: "IX_Channel_ScreenLayoutId",
                table: "Channel",
                column: "ScreenLayoutId");

            migrationBuilder.CreateIndex(
                name: "IX_ChannelFallbackSlate_ChannelId",
                table: "ChannelFallbackSlate",
                column: "ChannelId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ChannelFallbackSlate_CollectionId",
                table: "ChannelFallbackSlate",
                column: "CollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_ChannelFallbackSlate_MediaItemId",
                table: "ChannelFallbackSlate",
                column: "MediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_ChannelFallbackSlate_PlaylistId",
                table: "ChannelFallbackSlate",
                column: "PlaylistId");

            migrationBuilder.CreateIndex(
                name: "IX_CommercialPreset_CollectionId",
                table: "CommercialPreset",
                column: "CollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_CommercialPreset_MediaItemId",
                table: "CommercialPreset",
                column: "MediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_ExternalCollection_CollectionId",
                table: "ExternalCollection",
                column: "CollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_MediaSkip_MediaItemId",
                table: "MediaSkip",
                column: "MediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_PlaylistItemCommercial_CommercialPresetId",
                table: "PlaylistItemCommercial",
                column: "CommercialPresetId");

            migrationBuilder.CreateIndex(
                name: "IX_PlaylistItemCommercial_PlaylistItemId",
                table: "PlaylistItemCommercial",
                column: "PlaylistItemId");

            migrationBuilder.CreateIndex(
                name: "IX_PlayoutCalendarRule_PlayoutId",
                table: "PlayoutCalendarRule",
                column: "PlayoutId");

            migrationBuilder.CreateIndex(
                name: "IX_ProgramScheduleItemCommercial_CommercialPresetId",
                table: "ProgramScheduleItemCommercial",
                column: "CommercialPresetId");

            migrationBuilder.CreateIndex(
                name: "IX_ProgramScheduleItemCommercial_ProgramScheduleItemId",
                table: "ProgramScheduleItemCommercial",
                column: "ProgramScheduleItemId");

            migrationBuilder.CreateIndex(
                name: "IX_ScreenLayoutElement_ParentElementId",
                table: "ScreenLayoutElement",
                column: "ParentElementId");

            migrationBuilder.CreateIndex(
                name: "IX_ScreenLayoutElement_ScreenLayoutId",
                table: "ScreenLayoutElement",
                column: "ScreenLayoutId");

            migrationBuilder.CreateIndex(
                name: "IX_ScreenLayoutRule_ElementId",
                table: "ScreenLayoutRule",
                column: "ElementId");

            migrationBuilder.CreateIndex(
                name: "IX_ScreenLayoutRule_ScreenLayoutId",
                table: "ScreenLayoutRule",
                column: "ScreenLayoutId");

            migrationBuilder.AddForeignKey(
                name: "FK_Channel_ScreenLayout_ScreenLayoutId",
                table: "Channel",
                column: "ScreenLayoutId",
                principalTable: "ScreenLayout",
                principalColumn: "Id",
                onDelete: ReferentialAction.SetNull);

            migrationBuilder.AddForeignKey(
                name: "FK_Playout_ScreenLayout_ScreenLayoutId",
                table: "Playout",
                column: "ScreenLayoutId",
                principalTable: "ScreenLayout",
                principalColumn: "Id",
                onDelete: ReferentialAction.SetNull);

            migrationBuilder.AddForeignKey(
                name: "FK_ProgramScheduleItem_ScreenLayout_ScreenLayoutId",
                table: "ProgramScheduleItem",
                column: "ScreenLayoutId",
                principalTable: "ScreenLayout",
                principalColumn: "Id",
                onDelete: ReferentialAction.SetNull);

            migrationBuilder.Sql(
                """
                INSERT INTO CommercialPreset (Name, Kind, CollectionId, MediaItemId, PadSeconds, StrictDuration, PlaybackOrder)
                SELECT Name, 0, CollectionId, MediaItemId, 0, 0, 0
                FROM FillerPreset;
                """);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Channel_ScreenLayout_ScreenLayoutId",
                table: "Channel");

            migrationBuilder.DropForeignKey(
                name: "FK_Playout_ScreenLayout_ScreenLayoutId",
                table: "Playout");

            migrationBuilder.DropForeignKey(
                name: "FK_ProgramScheduleItem_ScreenLayout_ScreenLayoutId",
                table: "ProgramScheduleItem");

            migrationBuilder.DropTable(
                name: "ChannelFallbackSlate");

            migrationBuilder.DropTable(
                name: "ExternalCollection");

            migrationBuilder.DropTable(
                name: "MediaSkip");

            migrationBuilder.DropTable(
                name: "PlaylistItemCommercial");

            migrationBuilder.DropTable(
                name: "PlayoutCalendarRule");

            migrationBuilder.DropTable(
                name: "ProgramScheduleItemCommercial");

            migrationBuilder.DropTable(
                name: "ScreenLayoutRule");

            migrationBuilder.DropTable(
                name: "CommercialPreset");

            migrationBuilder.DropTable(
                name: "ScreenLayoutElement");

            migrationBuilder.DropTable(
                name: "ScreenLayout");

            migrationBuilder.DropIndex(
                name: "IX_Playout_ScreenLayoutId",
                table: "Playout");

            migrationBuilder.DropIndex(
                name: "IX_Channel_ScreenLayoutId",
                table: "Channel");

            migrationBuilder.DropColumn(
                name: "DurationMode",
                table: "ProgramScheduleItem");

            migrationBuilder.DropColumn(
                name: "FillCommercialGapsWithFillers",
                table: "ProgramScheduleItem");

            migrationBuilder.DropColumn(
                name: "ItemCount",
                table: "ProgramScheduleItem");

            migrationBuilder.DropColumn(
                name: "RespectMediaSkipChapters",
                table: "ProgramScheduleItem");

            migrationBuilder.DropColumn(
                name: "StartType",
                table: "ProgramScheduleItem");

            migrationBuilder.DropColumn(
                name: "TargetDuration",
                table: "ProgramScheduleItem");

            migrationBuilder.DropColumn(
                name: "SpecificDates",
                table: "ProgramScheduleAlternate");

            migrationBuilder.DropColumn(
                name: "CalendarMode",
                table: "Playout");

            migrationBuilder.DropColumn(
                name: "DaysToBuild",
                table: "Playout");

            migrationBuilder.DropColumn(
                name: "DeliveryMode",
                table: "Playout");

            migrationBuilder.DropColumn(
                name: "IsEnabled",
                table: "Playout");

            migrationBuilder.DropColumn(
                name: "PlayoutMode",
                table: "Playout");

            migrationBuilder.DropColumn(
                name: "ScreenLayoutId",
                table: "Playout");

            migrationBuilder.DropColumn(
                name: "SourceKind",
                table: "Playout");

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

            migrationBuilder.DropColumn(
                name: "OrderIndex",
                table: "CollectionItem");

            migrationBuilder.DropColumn(
                name: "Mode",
                table: "Channel");

            migrationBuilder.DropColumn(
                name: "ScreenLayoutId",
                table: "Channel");

            migrationBuilder.RenameColumn(
                name: "ScreenLayoutId",
                table: "ProgramScheduleItem",
                newName: "RerunCollectionId");

            migrationBuilder.RenameIndex(
                name: "IX_ProgramScheduleItem_ScreenLayoutId",
                table: "ProgramScheduleItem",
                newName: "IX_ProgramScheduleItem_RerunCollectionId");

            migrationBuilder.RenameColumn(
                name: "SourceId",
                table: "Playout",
                newName: "DecoId");

            migrationBuilder.AddColumn<string>(
                name: "Count",
                table: "ProgramScheduleMultipleItem",
                type: "longtext",
                nullable: true)
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.AddColumn<int>(
                name: "RerunCollectionId",
                table: "PlayoutProgramScheduleAnchor",
                type: "int",
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "BlockId",
                table: "PlayoutHistory",
                type: "int",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "BlockGroup",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BlockGroup", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "DecoGroup",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DecoGroup", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "DecoTemplateGroup",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DecoTemplateGroup", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "RerunCollection",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    CollectionId = table.Column<int>(type: "int", nullable: true),
                    MediaItemId = table.Column<int>(type: "int", nullable: true),
                    MultiCollectionId = table.Column<int>(type: "int", nullable: true),
                    SmartCollectionId = table.Column<int>(type: "int", nullable: true),
                    CollectionType = table.Column<int>(type: "int", nullable: false),
                    FirstRunPlaybackOrder = table.Column<int>(type: "int", nullable: false),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    RerunPlaybackOrder = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RerunCollection", x => x.Id);
                    table.ForeignKey(
                        name: "FK_RerunCollection_Collection_CollectionId",
                        column: x => x.CollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_RerunCollection_MediaItem_MediaItemId",
                        column: x => x.MediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_RerunCollection_MultiCollection_MultiCollectionId",
                        column: x => x.MultiCollectionId,
                        principalTable: "MultiCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_RerunCollection_SmartCollection_SmartCollectionId",
                        column: x => x.SmartCollectionId,
                        principalTable: "SmartCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "TemplateGroup",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TemplateGroup", x => x.Id);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Block",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    BlockGroupId = table.Column<int>(type: "int", nullable: false),
                    DateUpdated = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Minutes = table.Column<int>(type: "int", nullable: false),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    StopScheduling = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Block", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Block_BlockGroup_BlockGroupId",
                        column: x => x.BlockGroupId,
                        principalTable: "BlockGroup",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Deco",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    DeadAirFallbackCollectionId = table.Column<int>(type: "int", nullable: true),
                    DeadAirFallbackMediaItemId = table.Column<int>(type: "int", nullable: true),
                    DeadAirFallbackMultiCollectionId = table.Column<int>(type: "int", nullable: true),
                    DeadAirFallbackSmartCollectionId = table.Column<int>(type: "int", nullable: true),
                    DecoGroupId = table.Column<int>(type: "int", nullable: false),
                    DefaultFillerCollectionId = table.Column<int>(type: "int", nullable: true),
                    DefaultFillerMediaItemId = table.Column<int>(type: "int", nullable: true),
                    DefaultFillerMultiCollectionId = table.Column<int>(type: "int", nullable: true),
                    DefaultFillerSmartCollectionId = table.Column<int>(type: "int", nullable: true),
                    BreakContentMode = table.Column<int>(type: "int", nullable: false),
                    DeadAirFallbackCollectionType = table.Column<int>(type: "int", nullable: false),
                    DeadAirFallbackMode = table.Column<int>(type: "int", nullable: false),
                    DefaultFillerCollectionType = table.Column<int>(type: "int", nullable: false),
                    DefaultFillerMode = table.Column<int>(type: "int", nullable: false),
                    DefaultFillerTrimToFit = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    GraphicsElementsMode = table.Column<int>(type: "int", nullable: false),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    UseGraphicsElementsDuringFiller = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    UseWatermarkDuringFiller = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    WatermarkMode = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Deco", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Deco_Collection_DeadAirFallbackCollectionId",
                        column: x => x.DeadAirFallbackCollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Deco_Collection_DefaultFillerCollectionId",
                        column: x => x.DefaultFillerCollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Deco_DecoGroup_DecoGroupId",
                        column: x => x.DecoGroupId,
                        principalTable: "DecoGroup",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Deco_MediaItem_DeadAirFallbackMediaItemId",
                        column: x => x.DeadAirFallbackMediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Deco_MediaItem_DefaultFillerMediaItemId",
                        column: x => x.DefaultFillerMediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Deco_MultiCollection_DeadAirFallbackMultiCollectionId",
                        column: x => x.DeadAirFallbackMultiCollectionId,
                        principalTable: "MultiCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Deco_MultiCollection_DefaultFillerMultiCollectionId",
                        column: x => x.DefaultFillerMultiCollectionId,
                        principalTable: "MultiCollection",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Deco_SmartCollection_DeadAirFallbackSmartCollectionId",
                        column: x => x.DeadAirFallbackSmartCollectionId,
                        principalTable: "SmartCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Deco_SmartCollection_DefaultFillerSmartCollectionId",
                        column: x => x.DefaultFillerSmartCollectionId,
                        principalTable: "SmartCollection",
                        principalColumn: "Id");
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "DecoTemplate",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    DecoTemplateGroupId = table.Column<int>(type: "int", nullable: false),
                    DateUpdated = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DecoTemplate", x => x.Id);
                    table.ForeignKey(
                        name: "FK_DecoTemplate_DecoTemplateGroup_DecoTemplateGroupId",
                        column: x => x.DecoTemplateGroupId,
                        principalTable: "DecoTemplateGroup",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "RerunHistory",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    MediaItemId = table.Column<int>(type: "int", nullable: false),
                    PlayoutId = table.Column<int>(type: "int", nullable: false),
                    RerunCollectionId = table.Column<int>(type: "int", nullable: false),
                    When = table.Column<DateTime>(type: "datetime(6)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RerunHistory", x => x.Id);
                    table.ForeignKey(
                        name: "FK_RerunHistory_MediaItem_MediaItemId",
                        column: x => x.MediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_RerunHistory_Playout_PlayoutId",
                        column: x => x.PlayoutId,
                        principalTable: "Playout",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_RerunHistory_RerunCollection_RerunCollectionId",
                        column: x => x.RerunCollectionId,
                        principalTable: "RerunCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "Template",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    TemplateGroupId = table.Column<int>(type: "int", nullable: false),
                    DateUpdated = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    Name = table.Column<string>(type: "varchar(50)", maxLength: 50, nullable: true, collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Template", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Template_TemplateGroup_TemplateGroupId",
                        column: x => x.TemplateGroupId,
                        principalTable: "TemplateGroup",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "BlockItem",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    BlockId = table.Column<int>(type: "int", nullable: false),
                    CollectionId = table.Column<int>(type: "int", nullable: true),
                    MediaItemId = table.Column<int>(type: "int", nullable: true),
                    MultiCollectionId = table.Column<int>(type: "int", nullable: true),
                    SmartCollectionId = table.Column<int>(type: "int", nullable: true),
                    CollectionType = table.Column<int>(type: "int", nullable: false),
                    DisableWatermarks = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    IncludeInProgramGuide = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    Index = table.Column<int>(type: "int", nullable: false),
                    PlaybackOrder = table.Column<int>(type: "int", nullable: false),
                    SearchQuery = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    SearchTitle = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BlockItem", x => x.Id);
                    table.ForeignKey(
                        name: "FK_BlockItem_Block_BlockId",
                        column: x => x.BlockId,
                        principalTable: "Block",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_BlockItem_Collection_CollectionId",
                        column: x => x.CollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_BlockItem_MediaItem_MediaItemId",
                        column: x => x.MediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_BlockItem_MultiCollection_MultiCollectionId",
                        column: x => x.MultiCollectionId,
                        principalTable: "MultiCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_BlockItem_SmartCollection_SmartCollectionId",
                        column: x => x.SmartCollectionId,
                        principalTable: "SmartCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "DecoBreakContent",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    CollectionId = table.Column<int>(type: "int", nullable: true),
                    DecoId = table.Column<int>(type: "int", nullable: false),
                    MediaItemId = table.Column<int>(type: "int", nullable: true),
                    MultiCollectionId = table.Column<int>(type: "int", nullable: true),
                    PlaylistId = table.Column<int>(type: "int", nullable: true),
                    SmartCollectionId = table.Column<int>(type: "int", nullable: true),
                    CollectionType = table.Column<int>(type: "int", nullable: false),
                    Placement = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DecoBreakContent", x => x.Id);
                    table.ForeignKey(
                        name: "FK_DecoBreakContent_Collection_CollectionId",
                        column: x => x.CollectionId,
                        principalTable: "Collection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoBreakContent_Deco_DecoId",
                        column: x => x.DecoId,
                        principalTable: "Deco",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoBreakContent_MediaItem_MediaItemId",
                        column: x => x.MediaItemId,
                        principalTable: "MediaItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoBreakContent_MultiCollection_MultiCollectionId",
                        column: x => x.MultiCollectionId,
                        principalTable: "MultiCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoBreakContent_Playlist_PlaylistId",
                        column: x => x.PlaylistId,
                        principalTable: "Playlist",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoBreakContent_SmartCollection_SmartCollectionId",
                        column: x => x.SmartCollectionId,
                        principalTable: "SmartCollection",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "DecoGraphicsElement",
                columns: table => new
                {
                    DecoId = table.Column<int>(type: "int", nullable: false),
                    GraphicsElementId = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DecoGraphicsElement", x => new { x.DecoId, x.GraphicsElementId });
                    table.ForeignKey(
                        name: "FK_DecoGraphicsElement_Deco_DecoId",
                        column: x => x.DecoId,
                        principalTable: "Deco",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoGraphicsElement_GraphicsElement_GraphicsElementId",
                        column: x => x.GraphicsElementId,
                        principalTable: "GraphicsElement",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "DecoWatermark",
                columns: table => new
                {
                    DecoId = table.Column<int>(type: "int", nullable: false),
                    WatermarkId = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DecoWatermark", x => new { x.DecoId, x.WatermarkId });
                    table.ForeignKey(
                        name: "FK_DecoWatermark_ChannelWatermark_WatermarkId",
                        column: x => x.WatermarkId,
                        principalTable: "ChannelWatermark",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoWatermark_Deco_DecoId",
                        column: x => x.DecoId,
                        principalTable: "Deco",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "DecoTemplateItem",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    DecoId = table.Column<int>(type: "int", nullable: false),
                    DecoTemplateId = table.Column<int>(type: "int", nullable: false),
                    EndTime = table.Column<TimeSpan>(type: "time(6)", nullable: false),
                    StartTime = table.Column<TimeSpan>(type: "time(6)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DecoTemplateItem", x => x.Id);
                    table.ForeignKey(
                        name: "FK_DecoTemplateItem_DecoTemplate_DecoTemplateId",
                        column: x => x.DecoTemplateId,
                        principalTable: "DecoTemplate",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_DecoTemplateItem_Deco_DecoId",
                        column: x => x.DecoId,
                        principalTable: "Deco",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "PlayoutTemplate",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    DecoTemplateId = table.Column<int>(type: "int", nullable: true),
                    PlayoutId = table.Column<int>(type: "int", nullable: false),
                    TemplateId = table.Column<int>(type: "int", nullable: false),
                    DateUpdated = table.Column<DateTime>(type: "datetime(6)", nullable: false),
                    DaysOfMonth = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    DaysOfWeek = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    EndDay = table.Column<int>(type: "int", nullable: false),
                    EndMonth = table.Column<int>(type: "int", nullable: false),
                    EndYear = table.Column<int>(type: "int", nullable: true),
                    Index = table.Column<int>(type: "int", nullable: false),
                    LimitToDateRange = table.Column<bool>(type: "tinyint(1)", nullable: false),
                    MonthsOfYear = table.Column<string>(type: "longtext", nullable: true)
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    StartDay = table.Column<int>(type: "int", nullable: false),
                    StartMonth = table.Column<int>(type: "int", nullable: false),
                    StartYear = table.Column<int>(type: "int", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PlayoutTemplate", x => x.Id);
                    table.ForeignKey(
                        name: "FK_PlayoutTemplate_DecoTemplate_DecoTemplateId",
                        column: x => x.DecoTemplateId,
                        principalTable: "DecoTemplate",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_PlayoutTemplate_Playout_PlayoutId",
                        column: x => x.PlayoutId,
                        principalTable: "Playout",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_PlayoutTemplate_Template_TemplateId",
                        column: x => x.TemplateId,
                        principalTable: "Template",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "TemplateItem",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("MySql:ValueGenerationStrategy", MySqlValueGenerationStrategy.IdentityColumn),
                    BlockId = table.Column<int>(type: "int", nullable: false),
                    TemplateId = table.Column<int>(type: "int", nullable: false),
                    StartTime = table.Column<TimeSpan>(type: "time(6)", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TemplateItem", x => x.Id);
                    table.ForeignKey(
                        name: "FK_TemplateItem_Block_BlockId",
                        column: x => x.BlockId,
                        principalTable: "Block",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_TemplateItem_Template_TemplateId",
                        column: x => x.TemplateId,
                        principalTable: "Template",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "BlockItemGraphicsElement",
                columns: table => new
                {
                    BlockItemId = table.Column<int>(type: "int", nullable: false),
                    GraphicsElementId = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BlockItemGraphicsElement", x => new { x.BlockItemId, x.GraphicsElementId });
                    table.ForeignKey(
                        name: "FK_BlockItemGraphicsElement_BlockItem_BlockItemId",
                        column: x => x.BlockItemId,
                        principalTable: "BlockItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_BlockItemGraphicsElement_GraphicsElement_GraphicsElementId",
                        column: x => x.GraphicsElementId,
                        principalTable: "GraphicsElement",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "BlockItemWatermark",
                columns: table => new
                {
                    BlockItemId = table.Column<int>(type: "int", nullable: false),
                    WatermarkId = table.Column<int>(type: "int", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BlockItemWatermark", x => new { x.BlockItemId, x.WatermarkId });
                    table.ForeignKey(
                        name: "FK_BlockItemWatermark_BlockItem_BlockItemId",
                        column: x => x.BlockItemId,
                        principalTable: "BlockItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_BlockItemWatermark_ChannelWatermark_WatermarkId",
                        column: x => x.WatermarkId,
                        principalTable: "ChannelWatermark",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateIndex(
                name: "IX_PlayoutProgramScheduleAnchor_RerunCollectionId",
                table: "PlayoutProgramScheduleAnchor",
                column: "RerunCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_PlayoutHistory_BlockId",
                table: "PlayoutHistory",
                column: "BlockId");

            migrationBuilder.CreateIndex(
                name: "IX_Playout_DecoId",
                table: "Playout",
                column: "DecoId");

            migrationBuilder.CreateIndex(
                name: "IX_Block_BlockGroupId_Name",
                table: "Block",
                columns: new[] { "BlockGroupId", "Name" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_BlockGroup_Name",
                table: "BlockGroup",
                column: "Name",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_BlockItem_BlockId",
                table: "BlockItem",
                column: "BlockId");

            migrationBuilder.CreateIndex(
                name: "IX_BlockItem_CollectionId",
                table: "BlockItem",
                column: "CollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_BlockItem_MediaItemId",
                table: "BlockItem",
                column: "MediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_BlockItem_MultiCollectionId",
                table: "BlockItem",
                column: "MultiCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_BlockItem_SmartCollectionId",
                table: "BlockItem",
                column: "SmartCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_BlockItemGraphicsElement_GraphicsElementId",
                table: "BlockItemGraphicsElement",
                column: "GraphicsElementId");

            migrationBuilder.CreateIndex(
                name: "IX_BlockItemWatermark_WatermarkId",
                table: "BlockItemWatermark",
                column: "WatermarkId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DeadAirFallbackCollectionId",
                table: "Deco",
                column: "DeadAirFallbackCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DeadAirFallbackMediaItemId",
                table: "Deco",
                column: "DeadAirFallbackMediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DeadAirFallbackMultiCollectionId",
                table: "Deco",
                column: "DeadAirFallbackMultiCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DeadAirFallbackSmartCollectionId",
                table: "Deco",
                column: "DeadAirFallbackSmartCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DecoGroupId_Name",
                table: "Deco",
                columns: new[] { "DecoGroupId", "Name" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DefaultFillerCollectionId",
                table: "Deco",
                column: "DefaultFillerCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DefaultFillerMediaItemId",
                table: "Deco",
                column: "DefaultFillerMediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DefaultFillerMultiCollectionId",
                table: "Deco",
                column: "DefaultFillerMultiCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_Deco_DefaultFillerSmartCollectionId",
                table: "Deco",
                column: "DefaultFillerSmartCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoBreakContent_CollectionId",
                table: "DecoBreakContent",
                column: "CollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoBreakContent_DecoId",
                table: "DecoBreakContent",
                column: "DecoId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoBreakContent_MediaItemId",
                table: "DecoBreakContent",
                column: "MediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoBreakContent_MultiCollectionId",
                table: "DecoBreakContent",
                column: "MultiCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoBreakContent_PlaylistId",
                table: "DecoBreakContent",
                column: "PlaylistId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoBreakContent_SmartCollectionId",
                table: "DecoBreakContent",
                column: "SmartCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoGraphicsElement_GraphicsElementId",
                table: "DecoGraphicsElement",
                column: "GraphicsElementId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoGroup_Name",
                table: "DecoGroup",
                column: "Name",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_DecoTemplate_DecoTemplateGroupId_Name",
                table: "DecoTemplate",
                columns: new[] { "DecoTemplateGroupId", "Name" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_DecoTemplateGroup_Name",
                table: "DecoTemplateGroup",
                column: "Name",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_DecoTemplateItem_DecoId",
                table: "DecoTemplateItem",
                column: "DecoId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoTemplateItem_DecoTemplateId",
                table: "DecoTemplateItem",
                column: "DecoTemplateId");

            migrationBuilder.CreateIndex(
                name: "IX_DecoWatermark_WatermarkId",
                table: "DecoWatermark",
                column: "WatermarkId");

            migrationBuilder.CreateIndex(
                name: "IX_PlayoutTemplate_DecoTemplateId",
                table: "PlayoutTemplate",
                column: "DecoTemplateId");

            migrationBuilder.CreateIndex(
                name: "IX_PlayoutTemplate_PlayoutId",
                table: "PlayoutTemplate",
                column: "PlayoutId");

            migrationBuilder.CreateIndex(
                name: "IX_PlayoutTemplate_TemplateId",
                table: "PlayoutTemplate",
                column: "TemplateId");

            migrationBuilder.CreateIndex(
                name: "IX_RerunCollection_CollectionId",
                table: "RerunCollection",
                column: "CollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_RerunCollection_MediaItemId",
                table: "RerunCollection",
                column: "MediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_RerunCollection_MultiCollectionId",
                table: "RerunCollection",
                column: "MultiCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_RerunCollection_Name",
                table: "RerunCollection",
                column: "Name",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_RerunCollection_SmartCollectionId",
                table: "RerunCollection",
                column: "SmartCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_RerunHistory_MediaItemId",
                table: "RerunHistory",
                column: "MediaItemId");

            migrationBuilder.CreateIndex(
                name: "IX_RerunHistory_PlayoutId",
                table: "RerunHistory",
                column: "PlayoutId");

            migrationBuilder.CreateIndex(
                name: "IX_RerunHistory_RerunCollectionId",
                table: "RerunHistory",
                column: "RerunCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_Template_TemplateGroupId_Name",
                table: "Template",
                columns: new[] { "TemplateGroupId", "Name" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_TemplateGroup_Name",
                table: "TemplateGroup",
                column: "Name",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_TemplateItem_BlockId",
                table: "TemplateItem",
                column: "BlockId");

            migrationBuilder.CreateIndex(
                name: "IX_TemplateItem_TemplateId",
                table: "TemplateItem",
                column: "TemplateId");

            migrationBuilder.AddForeignKey(
                name: "FK_Playout_Deco_DecoId",
                table: "Playout",
                column: "DecoId",
                principalTable: "Deco",
                principalColumn: "Id",
                onDelete: ReferentialAction.SetNull);

            migrationBuilder.AddForeignKey(
                name: "FK_PlayoutHistory_Block_BlockId",
                table: "PlayoutHistory",
                column: "BlockId",
                principalTable: "Block",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_PlayoutProgramScheduleAnchor_RerunCollection_RerunCollection~",
                table: "PlayoutProgramScheduleAnchor",
                column: "RerunCollectionId",
                principalTable: "RerunCollection",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_ProgramScheduleItem_RerunCollection_RerunCollectionId",
                table: "ProgramScheduleItem",
                column: "RerunCollectionId",
                principalTable: "RerunCollection",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }
    }
}
