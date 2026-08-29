from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Select, Button, Label, Static
from textual.containers import Vertical, Horizontal


class EditChannelModal(ModalScreen[bool]):
    """Modal para editar as informações básicas de um canal."""
    
    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("EDITAR CANAL", id="modal-title")
            
            with Vertical(classes="input-group"):
                yield Label("Identificador (Código):")
                yield Input(id="channel-identifier")

            with Vertical(classes="input-group"):
                yield Label("Nome do Canal:")
                yield Input(id="channel-name")
            
            with Vertical(classes="input-group"):
                yield Label("Tipo:")
                yield Select(
                    [("TV", "TV"), ("Rádio", "RADIO")],
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
                    id="channel-mode"
                )
            
            with Horizontal(id="modal-actions"):
                yield Button("Salvar", variant="success", id="btn-save")
                yield Button("Cancelar", variant="error", id="btn-cancel")

    def on_mount(self) -> None:
        """Carrega os dados atuais do canal."""
        from app.database import SessionLocal
        from app.models import Channels
        
        with SessionLocal() as db:
            channel = db.get(Channels, self.channel_id)
            if channel:
                self.query_one("#channel-identifier", Input).value = channel.identifier or ""
                self.query_one("#channel-name", Input).value = channel.name
                self.query_one("#channel-type", Select).value = channel.type
                self.query_one("#channel-mode", Select).value = channel.execution_mode

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.save_changes()

    def save_changes(self) -> None:
        from app.database import SessionLocal
        from app.models import Channels
        
        identifier = self.query_one("#channel-identifier", Input).value.strip()
        name = self.query_one("#channel-name", Input).value.strip()
        ch_type = self.query_one("#channel-type", Select).value
        mode = self.query_one("#channel-mode", Select).value
        
        if not name or not identifier:
            return
            
        with SessionLocal() as db:
            channel = db.get(Channels, self.channel_id)
            if channel:
                # Opcional: verificar unicidade do identifier se mudou
                channel.identifier = identifier
                channel.name = name
                channel.type = ch_type
                channel.execution_mode = mode
                db.commit()
            
        self.dismiss(True)
