from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Label, RichLog, ProgressBar, ContentSwitcher
from textual.containers import Vertical, Horizontal
from app.engine import channel_runtimes
import psutil

class HomeScreen(Screen):
    """Single-Page Application (SPA) Mestre."""
    id = "home"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="spa-layout"):
            
            # Coluna Esquerda: Mini-Dash Persistente
            with Vertical(id="mini-dash"):
                
                with Vertical(classes="dash-panel"):
                    yield Static("SYSTEM STATUS", classes="panel-title")
                    yield Label("Env: Buscando...", id="lbl_env", classes="status-item")
                    yield Label("Motor: Buscando...", id="lbl_status", classes="status-item")
                
                with Vertical(classes="dash-panel"):
                    yield Static("HARDWARE", classes="panel-title")
                    with Horizontal(classes="metric-row"):
                        yield Label("CPU", classes="metric-label")
                        yield ProgressBar(total=100, show_eta=False, id="pb_cpu")
                    
                    with Horizontal(classes="metric-row"):
                        yield Label("RAM", classes="metric-label")
                        yield ProgressBar(total=100, show_eta=False, id="pb_ram")
                        
                with Vertical(classes="dash-panel last-panel"):
                    yield Static("LIVE TELEMETRY", classes="panel-title")
                    yield RichLog(id="live_logs", highlight=True, markup=True)

            # Coluna Direita: Workspace dinâmico
            with Vertical(id="workspace"):
                with ContentSwitcher(initial="status-view", id="main-switcher"):
                    
                    # Aba 1: Dashboard de Canais (Status)
                    with Vertical(id="status-view"):
                        yield Static("MOTORES DE TRANSMISSÃO ATIVOS", classes="panel-title")
                        yield Static("Buscando informações dos canais...", id="channels_status", markup=True)
                        
                    # Aba 2: Canais
                    with Vertical(id="channels-view"):
                        yield Static("Painel de Canais carregará aqui...", classes="placeholder-text")
                        
                    # Aba 3: Playlists
                    with Vertical(id="playlists-view"):
                        yield Static("Gerenciador de Playlists carregará aqui...", classes="placeholder-text")
                        
                    # Aba 4: Mídias
                    with Vertical(id="media-view"):
                        yield Static("Gerenciador de Mídias carregará aqui...", classes="placeholder-text")
                        
                    # Aba 5: Configurações
                    with Vertical(id="settings-view"):
                        yield Static("Painel de Configurações carregará aqui...", classes="placeholder-text")
                        
        yield Footer()

    def on_mount(self) -> None:
        self.update_telemetry()
        self.set_interval(2.0, self.update_telemetry)
        self.validate_environment()

    def validate_environment(self) -> None:
        try:
            deps = self.app.scanner.check_dependencies()
            all_ok = all(info.get("ok", False) for info in deps.values())
            lbl_env = self.query_one("#lbl_env", Label)
            if all_ok:
                lbl_env.update("Env: [bold #10b981]Validado[/]")
            else:
                lbl_env.update("Env: [bold #ef4444]Faltam Deps[/]")
        except Exception:
            self.query_one("#lbl_env", Label).update("Env: [bold #f59e0b]Alerta[/]")

    def update_telemetry(self) -> None:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        self.query_one("#pb_cpu", ProgressBar).update(progress=cpu)
        self.query_one("#pb_ram", ProgressBar).update(progress=ram)
        
        service = self.app.service
        is_running = service.is_running()
        lbl_status = self.query_one("#lbl_status", Label)
        if is_running:
            lbl_status.update(f"Motor: [bold #10b981]Online[/]")
        else:
            lbl_status.update(f"Motor: [bold #ef4444]Offline[/]")

        channels_str = ""
        if not channel_runtimes:
            channels_str = "[#64748b]Nenhum processo ativo.[/]"
        else:
            for cid, runtime in channel_runtimes.items():
                status = "[#10b981]ON[/]" if runtime.running else "[#ef4444]OFF[/]"
                channels_str += f"📺 Canal {cid} ➜ {status}\n"
        self.query_one("#channels_status", Static).update(channels_str)

        log_widget = self.query_one("#live_logs", RichLog)
        try:
            recent_logs = service.get_logs(lines=25)
            log_widget.clear()
            if recent_logs:
                log_widget.write(recent_logs)
            else:
                log_widget.write("[#64748b]Aguardando eventos...[/]")
        except Exception:
            log_widget.clear()
            log_widget.write("[bold #ef4444]SYSTEM FAULT: Falha ao ler logs.[/]")
