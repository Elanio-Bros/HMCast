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

# Mapa de navegação: view_atual -> view_anterior (para ESC voltar)
_VIEW_BACK_STACK = {
    "channel-detail":    "channels-manager",
    "channels-manager":  "home-menu",
    "playlist-detail":   "playlists-manager",
    "playlists-manager": "home-menu",
    "media-manager":     "home-menu",
    "settings-manager":  "home-menu",
}

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
        """Navegação por teclado.
        
        - ESC: Fecha modal ou volta view anterior (Regra de Ouro).
        - Setas VERTICAIS (up/down): navegam entre campos, exceto em
          DataTable, Select, OptionList, ListView, Tree (que têm navegação própria).
        - Setas HORIZONTAIS (left/right): navegam entre widgets, exceto em
          Input, DataTable, Select, Tree, SelectionList (cursor/colunas/expansão).
        """
        key = event.key
        
        # ═══════════════════════════════════════════
        #  PRIORIDADE ABSOLUTA: ESC
        # ═══════════════════════════════════════════
        if key == "escape":
            self.action_back()
            event.stop()
            event.prevent_default()
            return
        
        from textual.widgets import Input, DataTable, Select, OptionList, ListView, Tree
        from textual.widgets import SelectionList
        
        focused = self.focused
        
        # ――― Widgets com navegação VERTICAL interna ―――
        _vertical = (DataTable, Select, OptionList, ListView, Tree)
        
        if key == "down" and not isinstance(focused, _vertical):
            self.action_focus_next()
            event.stop()
            return
        
        if key == "up" and not isinstance(focused, _vertical):
            self.action_focus_previous()
            event.stop()
            return
        
        # ――― Widgets com navegação HORIZONTAL interna ―――
        _horizontal = (Input, DataTable, Select, Tree, SelectionList)
        
        if key == "right" and not isinstance(focused, _horizontal):
            self.action_focus_next()
            event.stop()
            return
        
        if key == "left" and not isinstance(focused, _horizontal):
            self.action_focus_previous()
            event.stop()
            return

    def action_back(self) -> None:
        """REGRA DE OURO: ESC é Voltar em qualquer lugar.
        
        Prioridades:
        1. Se há um ModalScreen aberto (ex: AddChannelModal), fecha o modal.
        2. Se está numa view detalhada, volta para a view anterior.
        3. Se está no menu principal, não faz nada.
        """
        # 1. Fechar modal — verifica pelo tipo da tela atual
        from textual.screen import ModalScreen
        if isinstance(self.screen, ModalScreen):
            self.pop_screen()
            return
        
        # 2. Navegação interna no ContentSwitcher
        try:
            from textual.widgets import ContentSwitcher
            switcher = self.screen.query_one(ContentSwitcher)
            current = switcher.current
            
            if current in _VIEW_BACK_STACK:
                switcher.current = _VIEW_BACK_STACK[current]
                # Foca automaticamente no primeiro card se voltou ao menu
                if _VIEW_BACK_STACK[current] == "home-menu":
                    self._focus_first_card()
        except Exception:
            pass

    def _focus_first_card(self) -> None:
        """Foca no primeiro card do menu principal."""
        try:
            card = self.screen.query_one("#card-channels")
            if card:
                card.focus()
        except Exception:
            pass

    def action_focus_view(self, view_id: str) -> None:
        """Ação auxiliar para views navegarem entre si via botões."""
        try:
            from textual.widgets import ContentSwitcher
            switcher = self.screen.query_one(ContentSwitcher)
            switcher.current = view_id
            self._auto_focus_view(view_id)
        except Exception:
            pass

    def _auto_focus_view(self, view_id: str) -> None:
        """Auto-foco inteligente ao entrar numa view."""
        try:
            container = self.screen.query_one(f"#{view_id}")
            # Tenta focar no primeiro DataTable
            table = container.query(DataTable).first()
            if table:
                table.focus()
                return
            # Tenta focar no primeiro botão de ação
            from textual.widgets import Button
            btn = container.query(Button).first()
            if btn:
                btn.focus()
        except Exception:
            pass
