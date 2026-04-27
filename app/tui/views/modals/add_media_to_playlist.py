from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Select, Button, Label, Static
from textual.containers import Vertical, Horizontal


class AddMediaToPlaylistModal(ModalScreen[bool]):
    """Modal para Adicionar Mídia a uma Playlist."""

    def __init__(self, playlist_id: int):
        super().__init__()
        self.playlist_id = playlist_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("ADICIONAR MÍDIA À PLAYLIST", id="modal-title")
            
            with Vertical(classes="input-group"):
                yield Label("Mídia (Arquivo):")
                yield Select([], id="select-media", prompt="Selecione um vídeo...")
            
            with Vertical(classes="input-group"):
                yield Label("Papel na Playlist:")
                yield Select([
                    ("Conteúdo", "CONTENT"),
                    ("Abertura", "OPENING"),
                    ("Encerramento", "CLOSING")
                ], id="select-role", value="CONTENT")
            
            yield Label("", id="m-pl-error-message", classes="error-text")
            
            with Horizontal(id="modal-actions"):
                yield Button("Adicionar", variant="success", id="btn-m-pl-save")
                yield Button("Cancelar", variant="error", id="btn-m-pl-cancel")

    def on_mount(self) -> None:
        from app.database import SessionLocal
        from app.models import MediaItem
        
        select = self.query_one("#select-media", Select)
        with SessionLocal() as db:
            medias = db.query(MediaItem).order_by(MediaItem.name).all()
            options = [(m.name, m.id) for m in medias]
            select.set_options(options)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-m-pl-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-m-pl-save":
            self.save_item()

    def save_item(self) -> None:
        from app.database import SessionLocal
        from app.models import PlaylistItem
        from sqlalchemy import func
        
        media_id = self.query_one("#select-media", Select).value
        role = self.query_one("#select-role", Select).value
        error_lab = self.query_one("#m-pl-error-message", Label)
        
        if not media_id:
            error_lab.update("Selecione uma mídia!")
            return

        with SessionLocal() as db:
            # Calcula próxima posição
            max_pos = db.query(func.max(PlaylistItem.position)).filter_by(playlist_id=self.playlist_id).scalar()
            next_pos = (max_pos + 1) if max_pos is not None else 0
            
            new_item = PlaylistItem(
                playlist_id=self.playlist_id,
                media_id=media_id,
                position=next_pos,
                role=role
            )
            db.add(new_item)
            db.commit()
            
        self.dismiss(True)
