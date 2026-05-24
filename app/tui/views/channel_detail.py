from textual.app import ComposeResult
from textual.widgets import Static, Button, Label, DataTable
from textual.containers import Vertical, Horizontal, Grid, VerticalScroll


class ChannelDetailView(Vertical):
    """View Detalhada com Exibição de Datas Inteligentes."""
    
    channel_id = None

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="detail-content-area"):
            with Horizontal(classes="view-header"):
                yield Static("DETALHES DO CANAL", classes="view-title", id="detail-title")
            
            with Vertical(id="detail-container", classes="detail-container"):
                with Grid(id="detail-info-grid", classes="info-grid"):
                    yield Label("ID:")
                    yield Static("-", id="lab-id")
                    yield Label("Código:")
                    yield Static("-", id="lab-identifier")
                    yield Label("Nome:")
                    yield Static("-", id="lab-name")
                    yield Label("Tipo:")
                    yield Static("-", id="lab-type")
                    yield Label("Status:")
                    yield Static("-", id="lab-status")

                with Horizontal(classes="section-header"):
                    yield Static("Programação Agendada", classes="section-label")

                yield DataTable(id="schedules-table")

        with Horizontal(classes="action-bar"):
            yield Button("Vincular Playlist", variant="success", id="btn-cd-add-schedule", classes="btn-action")
            yield Button("Editar", variant="warning", id="btn-detail-edit", classes="btn-action")
            yield Button("Voltar", id="btn-detail-back", classes="btn-action")

    def load_channel(self, channel_id: int) -> None:
        from app.database import SessionLocal
        from app.models import Channels, ChannelSchedule, Playlist
        
        self.channel_id = channel_id
        
        with SessionLocal() as db:
            channel = db.query(Channels).get(channel_id)
            if not channel:
                return
            
            self.query_one("#lab-id", Static).update(str(channel.id))
            self.query_one("#lab-identifier", Static).update(channel.identifier or "-")
            self.query_one("#lab-name", Static).update(channel.name)
            self.query_one("#lab-type", Static).update(channel.type)
            self.query_one("#lab-status", Static).update("ONLINE" if channel.active else "OFFLINE")
            
            title_text = channel.identifier if channel.identifier else channel.name
            self.query_one("#detail-title", Static).update(f"DETALHES: {title_text.upper()}")
            
            # Carrega horários
            table = self.query_one("#schedules-table", DataTable)
            table.zebra_stripes = True
            table.show_vertical_lines = True
            table.clear(columns=True)
            table.add_columns("Playlist", "Início", "Fim", "Data/Dias")
            
            schedules = db.query(ChannelSchedule).filter_by(channel_id=channel_id).all()
            for sch in schedules:
                playlist_name = db.query(Playlist).get(sch.playlist_id).name if sch.playlist_id else "-"
                
                # Consolida as informações de data/dias para exibição
                patterns = []
                if sch.weekdays: patterns.extend(sch.weekdays)
                if sch.month_days: patterns.extend([str(d) for d in sch.month_days])
                if sch.specific_dates: patterns.extend(sch.specific_dates)
                
                display_dates = ", ".join(patterns) if patterns else "Todo dia"
                
                table.add_row(
                    playlist_name,
                    sch.start_time.strftime("%H:%M"),
                    sch.end_time.strftime("%H:%M"),
                    display_dates
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-detail-back":
            self.app.action_focus_view("channels-manager")
        elif event.button.id == "btn-detail-edit":
            self.action_edit_channel()
        elif event.button.id == "btn-cd-add-schedule":
            self.action_add_schedule()

    def action_edit_channel(self) -> None:
        from app.tui.views.modals.edit_channel import EditChannelModal
        def check_result(success: bool) -> None:
            if success:
                self.load_channel(self.channel_id)
        self.app.push_screen(EditChannelModal(self.channel_id), check_result)

    def action_add_schedule(self) -> None:
        from app.tui.views.modals.add_schedule import AddScheduleModal
        def check_result(success: bool) -> None:
            if success:
                self.load_channel(self.channel_id)
        self.app.push_screen(AddScheduleModal(self.channel_id), check_result)
