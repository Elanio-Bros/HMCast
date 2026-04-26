from textual.app import ComposeResult
from textual.widgets import Static, Button, Label, DataTable
from textual.containers import Vertical, Horizontal, Grid


class ChannelDetailView(Vertical):
    """View detalhada que exibe o Código e ID do canal."""
    
    channel_id = None

    def compose(self) -> ComposeResult:
        with Horizontal(classes="view-header"):
            yield Static("DETALHES DO CANAL", classes="view-title", id="detail-title")
        
        with Vertical(id="detail-container"):
            with Grid(id="detail-info-grid"):
                yield Label("Código:")
                yield Static("-", id="lab-identifier")
                
                yield Label("ID Interno:")
                yield Static("-", id="lab-id")
                
                yield Label("Nome:")
                yield Static("-", id="lab-name")
                
                yield Label("Tipo:")
                yield Static("-", id="lab-type")
                
                yield Label("Status:")
                yield Static("-", id="lab-status")

            yield Static("Programação Agendada", classes="section-label")
            yield DataTable(id="schedules-table")

        with Horizontal(classes="action-bar"):
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
            
            # Atualiza labels
            self.query_one("#lab-identifier", Static).update(channel.identifier or "-")
            self.query_one("#lab-id", Static).update(str(channel.id))
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
            table.add_columns("Início", "Fim", "Playlist", "Dias")
            
            schedules = db.query(ChannelSchedule).filter_by(channel_id=channel_id).all()
            for sch in schedules:
                playlist_name = db.query(Playlist).get(sch.playlist_id).name if sch.playlist_id else "-"
                table.add_row(
                    sch.start_time.strftime("%H:%M"),
                    sch.end_time.strftime("%H:%M"),
                    playlist_name,
                    ", ".join(sch.weekdays) if sch.weekdays else "Todo dia"
                )
