from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Label, Input
from textual.containers import Vertical, Horizontal

class PromptModal(ModalScreen[str]):
    """Modal simples para entrada de texto (Renomear, etc)."""

    def __init__(self, title: str, initial_value: str = "", placeholder: str = ""):
        super().__init__()
        self.title_text = title
        self.initial_value = initial_value
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="prompt-container"):
            yield Static(self.title_text, id="prompt-title")
            yield Input(value=self.initial_value, placeholder=self.placeholder, id="prompt-input")
            with Horizontal(classes="prompt-footer"):
                yield Button("Cancelar", variant="error", id="btn-prompt-cancel")
                yield Button("Confirmar", variant="primary", id="btn-prompt-ok")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-prompt-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-prompt-ok":
            self.dismiss(self.query_one(Input).value)
