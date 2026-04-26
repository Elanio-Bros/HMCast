import psutil
import socket
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Vertical, Horizontal, VerticalScroll, Grid


class HomeScreen(Screen):
    """Tela inicial — Dashboard com foco em Transmissão."""
    id = "home"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Inicializa psutil
        psutil.cpu_percent(interval=None)
        self.last_net_io = psutil.net_io_counters()

    def get_local_ip(self):
        """Retorna o IP local da máquina."""
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

        with VerticalScroll(id="main-scroll"):

            # ── Cabeçalho Estendido (Focado em Transmissão) ──
            with Vertical(id="hero-section"):
                with Grid(id="system-metrics-grid"):
                    # Linha 1
                    yield Static("STATUS:", classes="m-label")
                    yield Static("INITIALIZING", id="status-val", classes="m-val")
                    
                    yield Static("CPU:", classes="m-label")
                    yield Static("0%", id="cpu-val", classes="m-val")
                    
                    yield Static("NET UP:", classes="m-label")
                    yield Static("0 KB/s", id="net-up-val", classes="m-val")

                    # Linha 2
                    yield Static("API URL:", classes="m-label")
                    yield Static("http://localhost:8000", id="api-url-val", classes="m-val")
                    
                    yield Static("MEM:", classes="m-label")
                    yield Static("0%", id="mem-val", classes="m-val")

                    yield Static("LOCAL IP:", classes="m-label")
                    yield Static(self.get_local_ip(), id="ip-val", classes="m-val ok")

            with Horizontal(classes="card-row"):
                with Horizontal(classes="card"):
                    yield Static("1", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Canais", classes="card-title")
                        yield Static("Broadcasting", classes="card-subtitle")
                        yield Static("Visualize e monitore todos os seus canais em tempo real.", classes="card-desc")
                
                with Horizontal(classes="card"):
                    yield Static("2", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Motor de Fluxo", classes="card-title")
                        yield Static("Service Manager", classes="card-subtitle")
                        yield Static("Controle o estado dos processos FFmpeg e estabilidade.", classes="card-desc")

            with Horizontal(classes="card-row"):
                with Horizontal(classes="card"):
                    yield Static("3", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Playlists", classes="card-title")
                        yield Static("Content", classes="card-subtitle")
                        yield Static("Organize seus vídeos e programe sequências automáticas.", classes="card-desc")
                
                with Horizontal(classes="card"):
                    yield Static("4", classes="card-number")
                    with Vertical(classes="card-content"):
                        yield Static("Midias", classes="card-title")
                        yield Static("Storage", classes="card-subtitle")
                        yield Static("Gerencie seus arquivos de vídeo e metadados.", classes="card-desc")

        yield Footer()

    def on_mount(self) -> None:
        """Inicia a atualização da telemetria."""
        self.update_metrics()
        self.set_interval(1.0, self.update_metrics)

    def format_bytes(self, n):
        """Formata bytes para KB/s ou MB/s."""
        if n < 1024: return f"{n} B/s"
        elif n < 1024 * 1024: return f"{n/1024:.1f} KB/s"
        else: return f"{n/(1024*1024):.1f} MB/s"

    def update_metrics(self) -> None:
        """Atualiza os valores de CPU, Memória, Rede e Status do Serviço."""
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            
            # Rede
            new_net_io = psutil.net_io_counters()
            sent_delta = new_net_io.bytes_sent - self.last_net_io.bytes_sent
            self.last_net_io = new_net_io
            
            # Atualiza widgets
            self.query_one("#cpu-val", Static).update(f"{cpu}%")
            self.query_one("#mem-val", Static).update(f"{mem}%")
            self.query_one("#net-up-val", Static).update(self.format_bytes(sent_delta))
            
            # Status do Serviço Real
            service = self.app.service
            status_widget = self.query_one("#status-val", Static)
            if service.is_running():
                status_widget.update("ONLINE")
                status_widget.set_classes("m-val ok")
            else:
                status_widget.update("OFFLINE")
                status_widget.set_classes("m-val error")
            
        except Exception as e:
            self.app.log.error(f"Erro na telemetria: {e}")
