from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label, Static, Switch
from textual.containers import Vertical, Horizontal


class EditPlaylistModal(ModalScreen[bool]):
    """Modal para Editar Playlist Existente."""

    def __init__(self, playlist_id: int):
        super().__init__()
        self.playlist_id = playlist_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("EDITAR PLAYLIST", id="modal-title")
            
            with Vertical(classes="input-group"):
                yield Label("Nome da Playlist:")
                yield Input(placeholder="Ex: Filmes de Ação", id="pl-edit-name")
            
            with Horizontal(classes="input-group-row"):
                yield Label("Modo Aleatório (Shuffle):")
                yield Switch(id="pl-edit-shuffle")
            
            yield Label("", id="pl-edit-error-message", classes="error-text")
            
            with Horizontal(id="modal-actions"):
                yield Button("Salvar Alterações", variant="success", id="btn-pl-update")
                yield Button("Cancelar", variant="error", id="btn-pl-edit-cancel")

    def on_mount(self) -> None:
        """Carrega os dados atuais da playlist."""
        from app.database import SessionLocal
        from app.models import Playlist
        
        with SessionLocal() as db:
            pl = db.query(Playlist).get(self.playlist_id)
            if pl:
                self.query_one("#pl-edit-name", Input).value = pl.name
                self.query_one("#pl-edit-shuffle", Switch).value = pl.shuffle

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pl-edit-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-pl-update":
            self.update_playlist()

    def update_playlist(self) -> None:
        from app.database import SessionLocal
        from app.models import Playlist
        
        name = self.query_one("#pl-edit-name", Input).value.strip()
        shuffle = self.query_one("#pl-edit-shuffle", Switch).value
        error_lab = self.query_one("#pl-edit-error-message", Label)
        
        if not name:
            error_lab.update("O nome da playlist é obrigatório!")
            return

        with SessionLocal() as db:
            pl = db.query(Playlist).get(self.playlist_id)
            if pl:
                pl.name = name
                pl.shuffle = shuffle
                db.commit()
            
        self.dismiss(True)
