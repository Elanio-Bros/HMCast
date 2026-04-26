from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Vertical, Horizontal


class MainMenuView(Vertical):
    """View que contém o grid principal de cards (Acesso Rápido)."""

    def compose(self) -> ComposeResult:
        with Vertical(id="home-menu"):
            with Horizontal(classes="card-row"):
                # Card Canais
                with Horizontal(classes="card", id="card-channels"):
                    yield Static("1", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Canais", classes="card-title")
                        yield Static("Broadcasting", classes="card-subtitle")
                        yield Static("Visualize e monitore todos os seus canais em tempo real.", classes="card-desc")
                
                # Card Motor
                with Horizontal(classes="card", id="card-motor"):
                    yield Static("2", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Motor de Fluxo", classes="card-title")
                        yield Static("Service Manager", classes="card-subtitle")
                        yield Static("Controle o estado dos processos FFmpeg e estabilidade.", classes="card-desc")

            with Horizontal(classes="card-row"):
                # Card Playlists
                with Horizontal(classes="card", id="card-playlists"):
                    yield Static("3", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Playlists", classes="card-title")
                        yield Static("Content", classes="card-subtitle")
                        yield Static("Organize seus vídeos e programe sequências automáticas.", classes="card-desc")
                
                # Card Mídias
                with Horizontal(classes="card", id="card-media"):
                    yield Static("4", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Midias", classes="card-title")
                        yield Static("Storage", classes="card-subtitle")
                        yield Static("Gerencie seus arquivos de vídeo e metadados.", classes="card-desc")

    def on_click(self, event) -> None:
        """Gerencia o clique nos cards e avisa a tela principal para trocar de view."""
        clicked_widget = event.widget
        
        # Se for o card de canais, pedimos para a HomeScreen trocar
        if clicked_widget.id == "card-channels" or self.is_descendant_of(clicked_widget, "card-channels"):
            # Acessamos a HomeScreen e trocamos a view
            self.app.screen.query_one("ContentSwitcher").current = "channels-manager"

    def is_descendant_of(self, widget, target_id):
        parent = widget.parent
        while parent:
            if parent.id == target_id:
                return True
            parent = parent.parent
        return False
