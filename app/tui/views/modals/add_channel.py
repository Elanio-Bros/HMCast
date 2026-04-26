from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Select, Button, Label, Static
from textual.containers import Vertical, Horizontal


class AddChannelModal(ModalScreen[bool]):
    """Modal flutuante para adicionar um novo canal com Identificador."""
    
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("ADICIONAR NOVO CANAL", id="modal-title")
            
            with Vertical(classes="input-group"):
                yield Label("Identificador (Código):")
                yield Input(placeholder="Ex: CH-01, NEWS, FILM", id="channel-identifier")

            with Vertical(classes="input-group"):
                yield Label("Nome do Canal:")
                yield Input(placeholder="Ex: Filmes 24h", id="channel-name")
            
            with Vertical(classes="input-group"):
                yield Label("Tipo:")
                yield Select(
                    [("TV", "TV"), ("Rádio", "RADIO")],
                    value="TV",
                    id="channel-type"
                )
            
            with Vertical(classes="input-group"):
                yield Label("Modo de Execução:")
                yield Select(
                    [
                        ("Sob Demanda (On Demand)", "ON_DEMAND"),
                        ("Sempre Ativo (Always On)", "ALWAYS_ON"),
                        ("Preditivo", "PREDICTIVE")
                    ],
                    value="ON_DEMAND",
                    id="channel-mode"
                )
            
            with Horizontal(id="modal-actions"):
                yield Button("Salvar", variant="success", id="btn-save")
                yield Button("Cancelar", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.save_channel()

    def save_channel(self) -> None:
        from app.database import SessionLocal
        from app.models import Channels
        
        identifier = self.query_one("#channel-identifier", Input).value.strip()
        name = self.query_one("#channel-name", Input).value.strip()
        ch_type = self.query_one("#channel-type", Select).value
        mode = self.query_one("#channel-mode", Select).value
        
        if not name or not identifier:
            # Notificar usuário se campos obrigatórios faltarem
            return
            
        with SessionLocal() as db:
            # Verifica se o identificador já existe
            existing = db.query(Channels).filter_by(identifier=identifier).first()
            if existing:
                # Aqui poderíamos mostrar um erro no modal
                return

            new_channel = Channels(
                identifier=identifier,
                name=name,
                type=ch_type,
                execution_mode=mode,
                active=True
            )
            db.add(new_channel)
            db.commit()
            
        self.dismiss(True)
