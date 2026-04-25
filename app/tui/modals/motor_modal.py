from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option
from textual.containers import Vertical


class MotorModal(ModalScreen):
    """Modal de controle do motor/servidor."""
    
    def compose(self) -> ComposeResult:
        with Vertical(id="nav-modal-container"):
            yield Static("🔧  GERENCIAR MOTOR", id="nav-modal-title")
            yield OptionList(
                Option("[bold #10b981]🚀 Iniciar Servidor[/]",   id="opt_start"),
                Option("[bold #f59e0b]🔄 Reiniciar Servidor[/]", id="opt_restart"),
                Option("[bold #ef4444]🛑 Parar Servidor[/]",     id="opt_stop"),
                Option("[bold #64748b]⬅️  Voltar[/]",             id="opt_back"),
                id="motor-option-list"
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        opt_id = event.option.id
        service = self.app.service
        
        if opt_id == "opt_start":
            service.start()
            self.dismiss()
        elif opt_id == "opt_restart":
            service.stop()
            service.start()
            self.dismiss()
        elif opt_id == "opt_stop":
            service.stop()
            self.dismiss()
        else:
            # Voltar → sinaliza ao app para reabrir o NavigationModal
            self.dismiss("__back__")
