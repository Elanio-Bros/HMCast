from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import SelectionList, Button, Label, Static, Select
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal


class AddMediaToPlaylistModal(ModalScreen[bool]):
    """Modal para Adicionar Múltiplas Mídias a uma Playlist."""

    def __init__(self, playlist_id: int):
        super().__init__()
        self.playlist_id = playlist_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("VINCULAR MÍDIAS À PLAYLIST", id="modal-title")
            
            yield Label("Selecione os vídeos (Use ESPAÇO para marcar):")
            # SelectionList permite múltipla escolha
            yield SelectionList[int](id="selection-media")
            
            with Vertical(classes="input-group"):
                yield Label("Papel na Playlist (Para todos os selecionados):")
                yield Select([
                    ("Conteúdo", "CONTENT"),
                    ("Abertura", "OPENING"),
                    ("Encerramento", "CLOSING")
                ], id="select-role", value="CONTENT")
            
            yield Label("", id="m-pl-error-message", classes="error-text")
            
            with Horizontal(id="modal-actions"):
                yield Button("Adicionar Selecionados", variant="success", id="btn-m-pl-save")
                yield Button("Cancelar", variant="error", id="btn-m-pl-cancel")

    def on_mount(self) -> None:
        from app.database import SessionLocal
        from app.models import MediaItem
        
        selection_list = self.query_one("#selection-media", SelectionList)
        with SessionLocal() as db:
            medias = db.query(MediaItem).order_by(MediaItem.name).all()
            # Criamos a lista de seleções
            options = [Selection(m.name, m.id) for m in medias]
            selection_list.add_options(options)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-m-pl-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-m-pl-save":
            self.save_items()

    def save_items(self) -> None:
        from app.database import SessionLocal
        from app.models import PlaylistItem
        from sqlalchemy import func
        
        selected_ids = self.query_one("#selection-media", SelectionList).selected
        role = self.query_one("#select-role", Select).value
        error_lab = self.query_one("#m-pl-error-message", Label)
        
        if not selected_ids:
            error_lab.update("Selecione ao menos uma mídia!")
            return

        with SessionLocal() as db:
            # Busca a última posição atual na playlist
            max_pos = db.query(func.max(PlaylistItem.position)).filter_by(playlist_id=self.playlist_id).scalar()
            current_pos = (max_pos + 1) if max_pos is not None else 0
            
            for media_id in selected_ids:
                new_item = PlaylistItem(
                    playlist_id=self.playlist_id,
                    media_id=media_id,
                    position=current_pos,
                    role=role
                )
                db.add(new_item)
                current_pos += 1 # Incrementa a posição para o próximo vídeo
            
            db.commit()
            
        self.dismiss(True)
