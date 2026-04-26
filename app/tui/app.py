from textual.app import App
from textual.theme import Theme
from app.database import SessionLocal
from app.media_utils import MediaUtils
from app.service_manager import ServiceManager
from app.tui.views.home import HomeScreen

# ══════════════════════════════════
# Tema personalizado: "Broadcast"
# Inspirado em dashboards de monitoramento de TV
# ══════════════════════════════════
BROADCAST_THEME = Theme(
    name="broadcast",
    primary="#a1a1aa",       # Zinc 400 — cinza neutro para destaques
    secondary="#10b981",     # Emerald — status positivo
    accent="#71717a",        # Zinc 500 — acentos discretos
    warning="#f59e0b",
    error="#ef4444",
    success="#10b981",
    foreground="#e4e4e7",    # Zinc 200 — texto claro
    background="#18181b",    # Zinc 900 — fundo base escuro
    surface="#27272a",       # Zinc 800 — painéis
    panel="#3f3f46",         # Zinc 700 — bordas e divisores
    dark=True,
)


class HMCli(App):
    """Aplicativo Textual para gerenciar"""
    
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = ["css/main.tcss", "css/channels.tcss", "css/modal.tcss"]
    
    BINDINGS = [
        ("v", "pop_screen", "Voltar"),
        ("escape", "pop_screen", "Voltar"),
        ("q", "quit", "Sair"),
    ]
    
    SCREENS = {
        "home": HomeScreen,
    }

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

    def action_pop_screen(self) -> None:
        if len(self.screen_stack) > 2:
            self.pop_screen()