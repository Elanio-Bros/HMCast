from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Vertical, Horizontal, VerticalScroll


class MainMenuView(VerticalScroll):
    """View principal de cards. A navegação agora é gerenciada globalmente pelo App."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="card-row"):
            with Horizontal(classes="card", id="card-channels"):
                yield Static("1", classes="card-number")
                with Vertical(classes="card-content"):
                    yield Static("Canais", classes="card-title")
                    yield Static("Broadcasting", classes="card-subtitle")
                    yield Static("Visualize e monitore todos os seus canais em tempo real.", classes="card-desc")

            with Horizontal(classes="card", id="card-playlists"):
                yield Static("3", classes="card-number")
                with Vertical(classes="card-content"):
                    yield Static("Playlists", classes="card-title")
                    yield Static("Content", classes="card-subtitle")
                    yield Static("Organize seus vídeos e programe sequências automáticas.", classes="card-desc")

        with Horizontal(classes="card-row"):
            with Horizontal(classes="card", id="card-media"):
                yield Static("4", classes="card-number")
                with Vertical(classes="card-content"):
                    yield Static("Midias", classes="card-title")
                    yield Static("Storage", classes="card-subtitle")
                    yield Static("Gerencie seus arquivos de vídeo e metadados.", classes="card-desc")
            
            with Horizontal(classes="card", id="card-settings"):
                yield Static("2", classes="card-number")
                with Vertical(classes="card-content"):
                    yield Static("Configurações", classes="card-title")
                    yield Static("System Admin", classes="card-subtitle")
                    yield Static("Gerencie servidor, diagnósticos e ferramentas de manutenção.", classes="card-desc")

    def on_mount(self) -> None:
        """Habilita o foco nos cards."""
        for card in self.query(".card"):
            card.can_focus = True

    def on_click(self, event) -> None:
        """Clique do mouse."""
        self.handle_selection(event.widget)

    def on_key(self, event) -> None:
        """Gerencia apenas o ENTER, as setas são agora globais no app.py."""
        if event.key == "enter" and self.app.focused:
            self.handle_selection(self.app.focused)

    def handle_selection(self, widget) -> None:
        if not widget: return
        target = widget
        while target:
            if hasattr(target, "id"):
                if target.id == "card-channels":
                    self.app.screen.query_one("ContentSwitcher").current = "channels-manager"
                    break
                elif target.id == "card-playlists":
                    self.app.screen.query_one("ContentSwitcher").current = "playlists-manager"
                    break
                elif target.id == "card-media":
                    self.app.screen.query_one("ContentSwitcher").current = "media-manager"
                    break
                elif target.id == "card-settings":
                    self.app.screen.query_one("ContentSwitcher").current = "settings-manager"
                    break
            target = target.parent

    def is_descendant_of(self, widget, target_id):
        parent = widget.parent
        while parent:
            if hasattr(parent, "id") and parent.id == target_id:
                return True
            parent = parent.parent
        return False
