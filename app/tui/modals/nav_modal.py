from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option
from textual.containers import Vertical


class NavigationModal(ModalScreen):
    """Modal flutuante de navegação principal."""
    
    def compose(self) -> ComposeResult:
        with Vertical(id="nav-modal-container"):
            yield Static("󰍜 MENU PRINCIPAL", id="nav-modal-title")
            yield OptionList(
                Option("[bold #10b981]🏠 Dashboard[/]",        id="opt_dashboard"),
                Option("[bold #10b981]📡 Canais[/]",            id="opt_channels"),
                Option("[bold #10b981]📑 Playlists[/]",         id="opt_playlists"),
                Option("[bold #10b981]🎬 Mídias[/]",            id="opt_media"),
                Option("[bold #f59e0b]🔧 Motor[/]",             id="opt_motor"),
                Option("[bold #94a3b8]⚙️  Configurações[/]",   id="opt_settings"),
                Option("[bold #ef4444]⬅️  Voltar[/]",           id="opt_back"),
                id="nav-option-list"
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        opt_id = event.option.id
        
        route = {
            "opt_dashboard": "status-view",
            "opt_channels":  "channels-view",
            "opt_playlists": "playlists-view",
            "opt_media":     "media-view",
            "opt_settings":  "settings-view",
        }
        
        if opt_id in route:
            self.dismiss(route[opt_id])
        elif opt_id == "opt_motor":
            self.dismiss("__motor__")
        else:
            self.dismiss(None)
