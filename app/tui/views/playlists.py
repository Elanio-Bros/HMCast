from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Button
from textual.containers import Vertical, Horizontal, VerticalScroll


class PlaylistsView(Vertical):
    """View de Listagem de Playlists (Padronizada com Canais)."""
    
    current_offset = 0
    page_size = 100
    has_more = True
    is_loading = False
    
    def compose(self) -> ComposeResult:
        # ── ÁREA ROLÁVEL (Regra de Ouro 1) ──
        with VerticalScroll(id="playlists-content-area"):
            with Horizontal(classes="view-header"):
                yield Static("GERENCIAMENTO DE PLAYLISTS", classes="view-title")
            
            yield DataTable(id="playlists-table")
        
        # ── BARRA DE AÇÕES FIXA (Sticky Footer) ──
        with Horizontal(classes="action-bar"):
            yield Button("Gerenciar Itens", variant="primary", id="btn-detail-playlist", classes="btn-action")
            yield Button("Nova Playlist", variant="success", id="btn-add-playlist", classes="btn-action")
            yield Button("Excluir", variant="error", id="btn-delete-playlist", classes="btn-action")
            yield Button("Voltar", id="btn-back-home", classes="btn-action")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.zebra_stripes = True
        table.show_vertical_lines = True
        table.cursor_type = "row"
        
        table.add_column("ID", width=5)
        table.add_column("Nome da Playlist", width=40)
        table.add_column("Qtd. Itens", width=15)
        table.add_column("Shuffle", width=15)
        
        self.refresh_playlists()
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

    def refresh_playlists(self) -> None:
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
        from app.models import Playlist, PlaylistItem
        from sqlalchemy import func
        
        table = self.query_one(DataTable)
        
        with SessionLocal() as db:
            playlists = db.query(Playlist).order_by(Playlist.id.desc()).offset(self.current_offset).limit(self.page_size).all()
            
            if len(playlists) < self.page_size:
                self.has_more = False
                
            self.current_offset += len(playlists)
            
            rows_to_add = []
            for pl in playlists:
                count = db.query(func.count(PlaylistItem.id)).filter_by(playlist_id=pl.id).scalar()
                shuffle_str = "● ATIVO" if pl.shuffle else "○ INATIVO"
                
                rows_to_add.append((
                    str(pl.id),
                    pl.name.upper(),
                    f"{count} mídias",
                    shuffle_str
                ))
                
            try:
                table.add_rows(rows_to_add)
            except Exception:
                pass
                
        self.is_loading = False

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Abre detalhes ao pressionar ENTER ou clicar duas vezes."""
        table = self.query_one(DataTable)
        row_data = table.get_row_at(event.cursor_row)
        playlist_id = int(row_data[0])
        from app.tui.views.playlist_detail import PlaylistDetailView
        from textual.widgets import ContentSwitcher
        
        switcher = self.app.screen.query_one(ContentSwitcher)
        detail_view = self.app.screen.query_one("#playlist-detail", PlaylistDetailView)
        detail_view.load_playlist(playlist_id)
        switcher.current = "playlist-detail"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back-home":
            self.app.screen.query_one("ContentSwitcher").current = "home-menu"
        elif event.button.id == "btn-add-playlist":
            self.action_add_playlist()
        elif event.button.id == "btn-detail-playlist":
            self.action_detail_playlist()
        elif event.button.id == "btn-delete-playlist":
            self.action_delete_playlist()

    def action_detail_playlist(self) -> None:
        table = self.query_one(DataTable)
        try:
            row_index = table.cursor_row
            row_data = table.get_row_at(row_index)
            playlist_id = int(row_data[0])
            from app.tui.views.playlist_detail import PlaylistDetailView
            from textual.widgets import ContentSwitcher
            
            switcher = self.app.screen.query_one(ContentSwitcher)
            detail_view = self.app.screen.query_one("#playlist-detail", PlaylistDetailView)
            detail_view.load_playlist(playlist_id)
            switcher.current = "playlist-detail"
        except Exception:
            pass

    def action_add_playlist(self) -> None:
        from app.tui.views.modals.add_playlist import AddPlaylistModal
        def check_result(success: bool) -> None:
            if success:
                self.refresh_playlists()
        self.app.push_screen(AddPlaylistModal(), check_result)

    def action_delete_playlist(self) -> None:
        from app.database import SessionLocal
        from app.models import Playlist, PlaylistItem
        table = self.query_one(DataTable)
        try:
            row_index = table.cursor_row
            row_data = table.get_row_at(row_index)
            playlist_id = int(row_data[0])
            with SessionLocal() as db:
                db.query(PlaylistItem).filter_by(playlist_id=playlist_id).delete()
                pl = db.query(Playlist).get(playlist_id)
                if pl:
                    db.delete(pl)
                    db.commit()
                    self.refresh_playlists()
        except Exception:
            pass
