from textual.app import ComposeResult
from textual.widgets import Static, Button, Label, DataTable
from textual.containers import Vertical, Horizontal, Grid, VerticalScroll


class PlaylistDetailView(Vertical):
    """Gerenciador de Itens da Playlist."""
    
    playlist_id = None

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="playlist-detail-content-area"):
            with Horizontal(classes="view-header"):
                yield Static("DETALHES DA PLAYLIST", classes="view-title", id="playlist-detail-title")
            
            with Vertical(id="playlist-detail-container", classes="detail-container"):
                with Grid(id="playlist-info-grid", classes="info-grid"):
                    yield Label("ID:")
                    yield Static("-", id="pl-lab-id")
                    yield Label("Nome:")
                    yield Static("-", id="pl-lab-name")
                    yield Label("Shuffle:")
                    yield Static("-", id="pl-lab-shuffle")

                with Horizontal(classes="section-header"):
                    yield Static("Fila de Reprodução (Vídeos)", classes="section-label")

                yield DataTable(id="playlist-items-table")

        with Horizontal(classes="action-bar"):
            yield Button("Vincular Mídia", variant="success", id="btn-add-media", classes="btn-action")
            yield Button("Editar", variant="warning", id="btn-edit-playlist-detail", classes="btn-action")
            yield Button("Mover Subir", variant="primary", id="btn-move-up", classes="btn-action")
            yield Button("Mover Descer", variant="primary", id="btn-move-down", classes="btn-action")
            yield Button("Remover", variant="error", id="btn-remove-item", classes="btn-action")
            yield Button("Voltar", id="btn-pl-detail-back", classes="btn-action")

    def load_playlist(self, playlist_id: int) -> None:
        from app.database import SessionLocal
        from app.models import Playlist, PlaylistItem, MediaItem
        
        self.playlist_id = playlist_id
        
        with SessionLocal() as db:
            pl = db.query(Playlist).get(playlist_id)
            if not pl:
                return
            
            self.query_one("#pl-lab-id", Static).update(str(pl.id))
            self.query_one("#pl-lab-name", Static).update(pl.name)
            self.query_one("#pl-lab-shuffle", Static).update("ATIVADO" if pl.shuffle else "DESATIVADO")
            self.query_one("#playlist-detail-title", Static).update(f"PLAYLIST: {pl.name.upper()}")
            
            # Carrega itens
            table = self.query_one("#playlist-items-table", DataTable)
            table.zebra_stripes = True
            table.show_vertical_lines = True
            table.clear(columns=True)
            table.add_columns("Pos", "Título", "Papel (Role)", "Duração")
            
            items = (
                db.query(PlaylistItem, MediaItem)
                .join(MediaItem, MediaItem.id == PlaylistItem.media_id)
                .filter(PlaylistItem.playlist_id == playlist_id)
                .order_by(PlaylistItem.position.asc())
                .all()
            )
            
            for p_item, m_item in items:
                duration_m = f"{m_item.duration // 60}:{m_item.duration % 60:02d}"
                table.add_row(
                    str(p_item.position),
                    m_item.name,
                    p_item.role,
                    duration_m,
                    key=str(p_item.id)
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pl-detail-back":
            self.app.screen.query_one("ContentSwitcher").current = "playlists-manager"
        elif event.button.id == "btn-edit-playlist-detail":
            self.action_edit_playlist()
        elif event.button.id == "btn-add-media":
            self.action_add_media()
        elif event.button.id == "btn-remove-item":
            self.action_remove_item()
        elif event.button.id in ["btn-move-up", "btn-move-down"]:
            self.action_reorder(event.button.id == "btn-move-up")

    def action_edit_playlist(self) -> None:
        from app.tui.views.modals.edit_playlist import EditPlaylistModal
        def check_result(success: bool) -> None:
            if success:
                self.load_playlist(self.playlist_id)
        self.app.push_screen(EditPlaylistModal(self.playlist_id), check_result)

    def action_add_media(self) -> None:
        from app.tui.views.modals.add_media_to_playlist import AddMediaToPlaylistModal
        def check_result(success: bool) -> None:
            if success:
                self.load_playlist(self.playlist_id)
        self.app.push_screen(AddMediaToPlaylistModal(self.playlist_id), check_result)

    def action_remove_item(self) -> None:
        from app.database import SessionLocal
        from app.models import PlaylistItem
        table = self.query_one(DataTable)
        try:
            item_id = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            with SessionLocal() as db:
                item = db.query(PlaylistItem).get(item_id)
                if item:
                    db.delete(item)
                    db.commit()
                    self.load_playlist(self.playlist_id)
        except Exception:
            pass

    def action_reorder(self, up: bool) -> None:
        from app.database import SessionLocal
        from app.models import PlaylistItem
        table = self.query_one(DataTable)
        try:
            item_id = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            with SessionLocal() as db:
                current_item = db.query(PlaylistItem).get(item_id)
                if not current_item: return
                
                new_pos = current_item.position - 1 if up else current_item.position + 1
                if new_pos < 0: return
                
                # Troca posição com o vizinho
                neighbor = db.query(PlaylistItem).filter_by(
                    playlist_id=self.playlist_id, 
                    position=new_pos
                ).first()
                
                if neighbor:
                    neighbor.position = current_item.position
                
                current_item.position = new_pos
                db.commit()
                self.load_playlist(self.playlist_id)
        except Exception:
            pass
