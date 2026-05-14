from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Button
from textual.containers import Vertical, Horizontal, VerticalScroll


class ChannelsView(Vertical):
    """View de Canais com suporte a rolagem e paginação."""
    
    current_offset = 0
    page_size = 100
    has_more = True
    is_loading = False
    
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
        table.add_column("ID")
        table.add_column("CÓDIGO")
        table.add_column("Status")
        table.add_column("Nome")
        table.add_column("Tipo")
        table.add_column("Modo")
        
        table.zebra_stripes = True
        table.show_vertical_lines = True
        table.show_lines = True
        table.cursor_type = "row"
        self.refresh_channels()
        self.set_interval(0.5, self.check_scroll_for_pagination)

    def check_scroll_for_pagination(self) -> None:
        if not self.has_more or self.is_loading:
            return
            
        try:
            table = self.query_one(DataTable)
            at_bottom_scroll = table.scroll_y >= table.max_scroll_y - 10
            at_bottom_cursor = (table.cursor_row is not None and table.cursor_row >= table.row_count - 10)
            
            if at_bottom_scroll or at_bottom_cursor:
                self.load_page()
        except Exception:
            pass

    def refresh_channels(self) -> None:
        self.current_offset = 0
        self.has_more = True
        
        table = self.query_one(DataTable)
        table.clear()
        
        self.load_page()

    def load_page(self) -> None:
        if self.is_loading or not self.has_more:
            return
            
        self.is_loading = True
        from app.database import SessionLocal
        from app.models import Channels
        
        table = self.query_one(DataTable)
        
        with SessionLocal() as db:
            channels = db.query(Channels).order_by(Channels.id.desc()).offset(self.current_offset).limit(self.page_size).all()
            
            if len(channels) < self.page_size:
                self.has_more = False
                
            self.current_offset += len(channels)
            
            rows_to_add = []
            for ch in channels:
                status_str = "[ON] ONLINE" if ch.active else "[OFF] OFFLINE"
                rows_to_add.append((
                    str(ch.id),
                    ch.identifier or "-",
                    status_str,
                    ch.name,
                    ch.type,
                    ch.execution_mode
                ))
            try:
                table.add_rows(rows_to_add)
            except Exception:
                pass
                
        self.is_loading = False

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one(DataTable)
        row_data = table.get_row_at(event.cursor_row)
        channel_id = int(row_data[0])
        from app.tui.views.channel_detail import ChannelDetailView
        from textual.widgets import ContentSwitcher
        
        switcher = self.app.screen.query_one(ContentSwitcher)
        detail_view = self.app.screen.query_one("#channel-detail", ChannelDetailView)
        detail_view.load_channel(channel_id)
        switcher.current = "channel-detail"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-toggle-channel":
            self.action_toggle_channel()
        elif event.button.id == "btn-add-channel":
            self.action_add_channel()
        elif event.button.id == "btn-delete-channel":
            self.action_delete_channel()

    def action_add_channel(self) -> None:
        from app.tui.views.modals.add_channel import AddChannelModal
        def check_result(success: bool) -> None:
            if success:
                self.refresh_channels()
        self.app.push_screen(AddChannelModal(), check_result)

    def action_delete_channel(self) -> None:
        """Exclui o canal selecionado."""
        from app.database import SessionLocal
        from app.models import Channels
        
        table = self.query_one(DataTable)
        try:
            row_index = table.cursor_row
            row_data = table.get_row_at(row_index)
            channel_id = int(row_data[0])
            with SessionLocal() as db:
                channel = db.query(Channels).get(channel_id)
                if channel:
                    db.delete(channel)
                    db.commit()
                    self.refresh_channels()
        except Exception:
            pass

    def action_toggle_channel(self) -> None:
        from app.database import SessionLocal
        from app.models import Channels
        
        table = self.query_one(DataTable)
        try:
            row_index = table.cursor_row
            row_data = table.get_row_at(row_index)
            channel_id = int(row_data[0])
            with SessionLocal() as db:
                channel = db.query(Channels).get(channel_id)
                if channel:
                    channel.active = not channel.active
                    db.commit()
                    self.refresh_channels()
        except Exception:
            pass
