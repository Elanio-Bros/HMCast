from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label, Static, Switch
from textual.containers import Vertical, Horizontal


class AddPlaylistModal(ModalScreen[bool]):
    """Modal para Criar Nova Playlist."""

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("CRIAR NOVA PLAYLIST", id="modal-title")
            
            with Vertical(classes="input-group"):
                yield Label("Nome da Playlist:")
                yield Input(placeholder="Ex: Filmes de Ação", id="pl-name")
            
            with Horizontal(classes="input-group-row"):
                yield Label("Modo Aleatório (Shuffle):")
                yield Switch(id="pl-shuffle")
            
            # Label para mensagens de erro
            yield Label("", id="pl-error-message", classes="error-text")
            
            with Horizontal(id="modal-actions"):
                yield Button("Criar", variant="success", id="btn-pl-save")
                yield Button("Cancelar", variant="error", id="btn-pl-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pl-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-pl-save":
            self.save_playlist()

    def save_playlist(self) -> None:
        from app.database import SessionLocal
        from app.models import Playlist
        
        name = self.query_one("#pl-name", Input).value.strip()
        shuffle = self.query_one("#pl-shuffle", Switch).value
        error_lab = self.query_one("#pl-error-message", Label)
        
        if not name:
            error_lab.update("O nome da playlist é obrigatório!")
            return

        with SessionLocal() as db:
            new_pl = Playlist(name=name, shuffle=shuffle)
            db.add(new_pl)
            db.commit()
            
        self.dismiss(True)
