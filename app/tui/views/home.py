import psutil
import socket
import time

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ContentSwitcher
from textual.containers import Vertical, Horizontal, VerticalScroll, Grid

# Importamos as views isoladas
from app.tui.views.main_menu import MainMenuView
from app.tui.views.channels import ChannelsView
from app.tui.views.channel_detail import ChannelDetailView
from app.tui.views.playlists import PlaylistsView
from app.tui.views.playlist_detail import PlaylistDetailView
from app.tui.views.media import MediaView
from app.tui.views.settings import SettingsView


class HomeScreen(Screen):
    """
    Tela Principal (Orquestradora).
    Workspace agora é um Vertical simples, pois cada View interna gerencia seu próprio Scroll.
    """
    id = "home"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        psutil.cpu_percent(interval=None)
        self.last_net_io = psutil.net_io_counters()
        self.start_time = time.time()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # ── CABEÇALHO FIXO ──
        with Vertical(id="hero-section"):
            with Grid(id="system-metrics-grid"):
                yield Static("STATUS:", classes="m-label")
                yield Static("OFFLINE", id="status-val", classes="m-val error")
                yield Static("CPU:", classes="m-label")
                yield Static("0%", id="cpu-val", classes="m-val")
                yield Static("NET UP:", classes="m-label")
                yield Static("0 KB/s", id="net-up-val", classes="m-val")
                yield Static("API URL:", classes="m-label")
                yield Static("http://localhost:8000", id="api-url-val", classes="m-val")
                yield Static("MEM:", classes="m-label")
                yield Static("0%", id="mem-val", classes="m-val")
                yield Static("LOCAL IP:", classes="m-label")
                yield Static(self.get_local_ip(), id="ip-val", classes="m-val ok")

        # ── WORKSPACE (Container Pai) ──
        with Vertical(id="workspace"):
            with ContentSwitcher(initial="home-menu", id="view-switcher"):
                yield MainMenuView(id="home-menu")
                yield ChannelsView(id="channels-manager")
                yield ChannelDetailView(id="channel-detail")
                yield PlaylistsView(id="playlists-manager")
                yield PlaylistDetailView(id="playlist-detail")
                yield MediaView(id="media-manager")
                yield SettingsView(id="settings-manager")

        yield Footer()

    def on_mount(self) -> None:
        self.update_metrics()
        self.set_interval(1.0, self.update_metrics)

    def format_bytes(self, n):
        if n < 1024: return f"{n} B/s"
        elif n < 1024 * 1024: return f"{n/1024:.1f} KB/s"
        else: return f"{n/(1024*1024):.1f} MB/s"

    def update_metrics(self) -> None:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            new_net_io = psutil.net_io_counters()
            sent_delta = new_net_io.bytes_sent - self.last_net_io.bytes_sent
            self.last_net_io = new_net_io
            
            self.query_one("#cpu-val", Static).update(f"{cpu}%")
            self.query_one("#mem-val", Static).update(f"{mem}%")
            self.query_one("#net-up-val", Static).update(self.format_bytes(sent_delta))
            
            service = self.app.service
            status_widget = self.query_one("#status-val", Static)
            if service.is_running():
                status_widget.update("ONLINE")
                status_widget.set_classes("m-val ok")
            else:
                status_widget.update("OFFLINE")
                status_widget.set_classes("m-val error")
        except Exception:
            pass

    def on_button_pressed(self, event) -> None:
        if event.button.id == "btn-back-home":
            self.app.action_focus_view("home-menu")
