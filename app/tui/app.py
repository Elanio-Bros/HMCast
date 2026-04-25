from textual.app import App
from app.database import SessionLocal
from app.media_utils import MediaUtils
from app.service_manager import ServiceManager
from app.tui.screens.home import HomeScreen

from textual.screen import Screen
from textual.widgets import Header, Footer, Static

class DummyChannelsScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        yield Static("Tela de Canais em construção...")
        yield Footer()

class VideoTVApp(App):
    """Aplicativo Textual para gerenciar o Video TV."""
    
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = "css/main.tcss"
    
    BINDINGS = [
        ("m", "open_menu", "Menu"),
        ("v", "pop_screen", "Voltar"),
        ("escape", "pop_screen", "Voltar"),
        ("q", "quit", "Sair"),
    ]
    
    SCREENS = {
        "home": HomeScreen,
        "channels": DummyChannelsScreen,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injeção de dependência na raiz do App (acessível por qualquer Screen via self.app)
        self.db = SessionLocal()
        self.scanner = MediaUtils()
        self.service = ServiceManager()

    def on_mount(self) -> None:
        self.title = "Video TV"
        self.push_screen("home")

    def action_pop_screen(self) -> None:
        if len(self.screen_stack) > 2:
            self.pop_screen()

    def action_open_menu(self) -> None:
        from app.tui.modals.nav_modal import NavigationModal
        
        def handle_nav(view_name: str | None) -> None:
            if view_name == "__motor__":
                from app.tui.modals.motor_modal import MotorModal
                
                def after_motor(result: str | None) -> None:
                    if result == "__back__":
                        # Volta para o NavigationModal (reabrir)
                        self.call_after_refresh(self.action_open_menu)
                
                self.call_after_refresh(lambda: self.push_screen(MotorModal(), after_motor))
                return
            if view_name:
                from textual.widgets import ContentSwitcher
                try:
                    # Switch view on the ContentSwitcher
                    switcher = self.screen.query_one("#main-switcher", ContentSwitcher)
                    switcher.current = view_name
                except Exception:
                    pass
                        
        self.push_screen(NavigationModal(), handle_nav)
