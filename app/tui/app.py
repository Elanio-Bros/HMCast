from textual.app import App
from textual.theme import Theme
from app.database import SessionLocal
from app.media_utils import MediaUtils
from app.service_manager import ServiceManager
from app.tui.views.home import HomeScreen

# Tema Broadcast
BROADCAST_THEME = Theme(
    name="broadcast",
    primary="#a1a1aa",
    secondary="#10b981",
    accent="#71717a",
    warning="#f59e0b",
    error="#ef4444",
    success="#10b981",
    foreground="#e4e4e7",
    background="#18181b",
    surface="#27272a",
    panel="#3f3f46",
    dark=True,
)

class HMCli(App):
    """Aplicativo Central - Orquestrador de Regras Globais."""
    
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = ["css/main.tcss", "css/channels.tcss", "css/playlists.tcss", "css/media.tcss", "css/modal.tcss", "css/settings.tcss"]
    
    BINDINGS = [
        ("q", "quit", "Sair"),
        ("escape", "back", "Voltar"),
    ]
    
    SCREENS = {"home": HomeScreen}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = SessionLocal()
        self.scanner = MediaUtils()
        self.service = ServiceManager()

    def on_mount(self) -> None:
        self.register_theme(BROADCAST_THEME)
        self.theme = "broadcast"
        self.title = "HMC"
        self.sub_title = "Media Transmission System"
        self.push_screen("home")

    def on_key(self, event) -> None:
        """TERCEIRA REGRA: Navegação por setas ADICIONAL ao TAB."""
        key = event.key
        focused = self.focused
        
        # PRIORIDADE MÁXIMA: ESC (Garante a Regra 2 em Modais e Telas)
        if key == "escape":
            self.action_back()
            event.stop()            # Impede que o binding do App dispare de novo
            event.prevent_default() # Garante que o widget focado não use a tecla
            return

        # Widgets que possuem comportamento interno próprio para as setas
        from textual.widgets import Input, DataTable, Select, OptionList, ListView
        
        if key == "down":
            # Se não for uma lista/tabela, a seta para baixo pula para o próximo campo
            if not isinstance(focused, (DataTable, Select, OptionList, ListView)):
                self.action_focus_next()
        elif key == "up":
            # Seta para cima volta o foco
            if not isinstance(focused, (DataTable, Select, OptionList, ListView)):
                self.action_focus_previous()
        elif key == "right":
            # Seta direita avança o foco (exceto em texto/tabela)
            if not isinstance(focused, (Input, DataTable, OptionList)):
                self.action_focus_next()
        elif key == "left":
            # Seta esquerda retrocede o foco (exceto em texto/tabela)
            if not isinstance(focused, (Input, DataTable, OptionList)):
                self.action_focus_previous()

    def action_back(self) -> None:
        """REGRA DE OURO 2: ESC é Voltar em qualquer lugar."""
        # Se houver mais de 2 telas (Default + Home + Modal), fecha o modal
        if len(self.screen_stack) > 2:
            self.pop_screen()
            return
            
        # Se estiver na HomeScreen, volta a navegação interna
        from textual.widgets import ContentSwitcher
        try:
            # Procuramos o switcher na tela ativa
            switcher = self.screen.query_one(ContentSwitcher)
            if switcher.current == "channel-detail":
                switcher.current = "channels-manager"
            elif switcher.current == "channels-manager":
                switcher.current = "home-menu"
            elif switcher.current == "media-manager":
                switcher.current = "home-menu"
            elif switcher.current == "settings-manager":
                switcher.current = "home-menu"
        except Exception:
            pass