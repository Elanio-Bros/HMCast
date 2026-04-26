from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Button
from textual.containers import Vertical, Horizontal


class ChannelsView(Vertical):
    """View para gerenciamento de canais com Identificador personalizado."""
    
    def compose(self) -> ComposeResult:
        with Horizontal(classes="view-header"):
            yield Static("GERENCIAMENTO DE CANAIS", classes="view-title")
        
        yield DataTable(id="channels-table")
        
        with Horizontal(classes="action-bar"):
            yield Button("Adicionar", variant="success", id="btn-add-channel", classes="btn-action")
            yield Button("Ligar/Desligar", variant="warning", id="btn-toggle-channel", classes="btn-action")
            yield Button("Excluir", variant="error", id="btn-delete-channel", classes="btn-action")
            yield Button("Voltar", id="btn-back-home", classes="btn-action")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        # Substituímos ID por CÓDIGO como prioridade
        table.add_column("CÓDIGO", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Nome", justify="center")
        table.add_column("Tipo", justify="center")
        table.add_column("Modo", justify="center")
        
        table.zebra_stripes = True
        table.show_vertical_lines = True
        table.show_lines = True
        table.cursor_type = "row"
        self.refresh_channels()

    def refresh_channels(self) -> None:
        from app.database import SessionLocal
        from app.models import Channels
        
        table = self.query_one(DataTable)
        table.clear()
        
        with SessionLocal() as db:
            channels = db.query(Channels).all()
            for ch in channels:
                status_str = "[ON] ONLINE" if ch.active else "[OFF] OFFLINE"
                
                table.add_row(
                    ch.identifier if ch.identifier else str(ch.id), # Mostra o código ou ID se vazio
                    status_str,
                    ch.name,
                    ch.type,
                    ch.execution_mode,
                    key=str(ch.id) # Mantemos o ID real na RowKey para operações
                )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Ao selecionar uma linha, usa a row_key (ID do banco) para abrir detalhes."""
        channel_id = int(event.row_key.value)
        self.screen.switch_to_channel_detail(channel_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-toggle-channel":
            self.action_toggle_channel()
        elif event.button.id == "btn-add-channel":
            self.action_add_channel()

    def action_add_channel(self) -> None:
        from app.tui.views.modals.add_channel import AddChannelModal
        def check_result(success: bool) -> None:
            if success:
                self.refresh_channels()
        self.app.push_screen(AddChannelModal(), check_result)

    def action_toggle_channel(self) -> None:
        from app.database import SessionLocal
        from app.models import Channels
        
        table = self.query_one(DataTable)
        try:
            # Usamos row_key para pegar o ID real
            channel_id = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            
            with SessionLocal() as db:
                channel = db.query(Channels).get(channel_id)
                if channel:
                    channel.active = not channel.active
                    db.commit()
                    self.refresh_channels()
        except Exception:
            pass
