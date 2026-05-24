import os
import time
import shutil
from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import Static, Button, DataTable, Label
from textual.containers import Vertical, Horizontal, VerticalScroll, Grid

from app.database import SessionLocal
from app.models import Channels
from app.engine import channel_runtimes
from app.migrations import DatabaseMigrator


class SettingsView(Vertical):
    """View de Configurações do Sistema.

    Centraliza o controle do servidor, status do engine,
    diagnósticos do sistema e ferramentas de manutenção.
    """

    def compose(self) -> ComposeResult:
        # ── CABEÇALHO ──
        with Horizontal(classes="view-header"):
            yield Static("CONFIGURAÇÕES", classes="view-title")

        # ── CONTEÚDO ROLÁVEL ──
        with VerticalScroll(id="settings-content-area"):

            # ── SEÇÃO: Servidor ──
            with Vertical(id="server-section", classes="settings-section"):
                with Horizontal(classes="section-header"):
                    yield Static("SERVIDOR", classes="section-label")
                    yield Static(id="server-status-badge", classes="settings-badge")
                with Grid(id="server-info-grid", classes="settings-info-grid"):
                    yield Label("Status:", classes="settings-label")
                    yield Static("VERIFICANDO...", id="server-status-val", classes="settings-val")
                    yield Label("PID:", classes="settings-label")
                    yield Static("-", id="server-pid-val", classes="settings-val")
                    yield Label("API URL:", classes="settings-label")
                    yield Static("http://localhost:8000", id="server-url-val", classes="settings-val")
                with Horizontal(classes="settings-actions"):
                    yield Button("▶ Iniciar", variant="success", id="btn-srv-start", classes="btn-action")
                    yield Button("⏹ Parar", variant="error", id="btn-srv-stop", classes="btn-action")
                    yield Button("🔄 Reiniciar", variant="warning", id="btn-srv-restart", classes="btn-action")

            # ── SEÇÃO: Status dos Canais ──
            with Vertical(id="channels-section", classes="settings-section"):
                with Horizontal(classes="section-header"):
                    yield Static("CANAIS EM EXECUÇÃO", classes="section-label")
                yield DataTable(id="settings-channels-table")

            # ── SEÇÃO: Configurações Gerais ──
            with Vertical(id="env-section", classes="settings-section"):
                with Horizontal(classes="section-header"):
                    yield Static("CONFIGURAÇÕES GLOBAIS (ENV)", classes="section-label")
                with Grid(id="env-info-grid", classes="settings-info-grid"):
                    yield Label("Auto-Scan (s):", classes="settings-label")
                    yield Static(os.getenv("MEDIA_AUTO_SCAN_INTERVAL", "600"), id="setting-scan-interval", classes="settings-val")
                    yield Label("Warmup (s):", classes="settings-label")
                    yield Static(os.getenv("PREDICTIVE_WARMUP_INTERVAL", "300"), id="setting-warmup-interval", classes="settings-val")
                    yield Label("Timeout Playlist (s):", classes="settings-label")
                    yield Static(os.getenv("HLS_PLAYLIST_WARMUP_TIMEOUT", "15"), id="setting-playlist-timeout", classes="settings-val")

            # ── SEÇÃO: Ferramentas ──
            with Vertical(id="tools-section", classes="settings-section"):
                with Horizontal(classes="section-header"):
                    yield Static("FERRAMENTAS", classes="section-label")
                with Horizontal(classes="settings-actions"):
                    yield Button("📄 Ver Logs", id="btn-tool-logs", classes="btn-action")
                    yield Button("🩺 Diagnóstico", id="btn-tool-diagnostics", classes="btn-action")
                    yield Button("💾 Backup DB", id="btn-tool-backup", classes="btn-action")
                with Horizontal(classes="settings-actions"):
                    yield Button("🛠 Migrar/Reparar DB", id="btn-tool-migrate", classes="btn-action")

            # ── SEÇÃO: Log Viewer ──
            with Vertical(id="log-section", classes="settings-section"):
                with Horizontal(classes="section-header"):
                    yield Static("LOGS / RESULTADO", classes="section-label")
                    yield Button("✕ Fechar", variant="default", id="btn-tool-logs-close", classes="btn-action")
                yield Static("", id="settings-log-content", classes="settings-log-box")

        # ── BARRA DE AÇÕES ──
        with Horizontal(classes="action-bar"):
            yield Button("Voltar", id="btn-back-home", classes="btn-action")

    def on_mount(self) -> None:
        """Inicializa a tabela de canais e dispara atualização periódica."""
        table = self.query_one("#settings-channels-table", DataTable)
        table.add_columns("Canal ID", "Nome", "Status", "Processo")
        table.zebra_stripes = True
        table.show_vertical_lines = True
        table.cursor_type = "row"

        self._update_server_status()
        self._update_channels_table()
        self.set_interval(2.0, self._tick_status)

    def _tick_status(self) -> None:
        """Atualização periódica dos status (servidor + canais)."""
        self._update_server_status()
        self._update_channels_table()

    # ──────────────────────────────────────────────
    #  SERVIDOR
    # ──────────────────────────────────────────────

    def _update_server_status(self) -> None:
        """Atualiza os indicadores de status do servidor."""
        service = self.app.service
        running = service.is_running()
        status_text = "ONLINE" if running else "OFFLINE"
        badge = self.query_one("#server-status-badge", Static)
        badge.update(f" {status_text} ")
        badge.set_classes("settings-badge ok" if running else "settings-badge error")

        status_val = self.query_one("#server-status-val", Static)
        status_val.update(service.get_status())

        pid_val = self.query_one("#server-pid-val", Static)
        if running:
            try:
                with open(service.pid_file, "r") as f:
                    pid_val.update(f.read().strip())
            except Exception:
                pid_val.update("?")
        else:
            pid_val.update("-")

    # ──────────────────────────────────────────────
    #  CANAIS
    # ──────────────────────────────────────────────

    def _update_channels_table(self) -> None:
        """Atualiza a tabela de canais com o runtime atual do engine."""
        table = self.query_one("#settings-channels-table", DataTable)
        table.clear()

        if not channel_runtimes:
            table.add_rows([("-", "-", "[dim]Nenhum canal rodando[/]", "-")])
            return

        rows = []
        for cid, runtime in channel_runtimes.items():
            status = "[green]ATIVO[/]" if runtime.running else "[red]PARADO[/]"
            proc = "[green]FFMPEG[/]" if (runtime.player.process and runtime.player.process.poll() is None) else "[dim]OFFLINE[/]"
            rows.append((str(cid), runtime.channel.name if hasattr(runtime, 'channel') else f"Canal {cid}", status, proc))

        try:
            table.add_rows(rows)
        except Exception:
            pass

    # ──────────────────────────────────────────────
    #  EVENTOS DOS BOTÕES
    # ──────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-back-home":
            self.app.screen.query_one("ContentSwitcher").current = "home-menu"

        elif btn_id == "btn-srv-start":
            self._action_start_server()

        elif btn_id == "btn-srv-stop":
            self._action_stop_server()

        elif btn_id == "btn-srv-restart":
            self._action_restart_server()

        elif btn_id == "btn-tool-logs":
            self._action_show_logs()

        elif btn_id == "btn-tool-logs-close":
            self.query_one("#log-section").display = False

        elif btn_id == "btn-tool-diagnostics":
            self._action_run_diagnostics()

        elif btn_id == "btn-tool-backup":
            self._action_backup_db()

        elif btn_id == "btn-tool-migrate":
            self._action_migrate_db()

    # ──────────────────────────────────────────────
    #  AÇÕES DO SERVIDOR
    # ──────────────────────────────────────────────

    def _action_start_server(self) -> None:
        service = self.app.service
        success, msg = service.start_service()
        severity = "success" if success else "warning"
        self.app.notify(msg, severity=severity)
        self._update_server_status()

    def _action_stop_server(self) -> None:
        service = self.app.service
        success, msg = service.stop_service()
        severity = "success" if success else "warning"
        self.app.notify(msg, severity=severity)
        self._update_server_status()

    def _action_restart_server(self) -> None:
        service = self.app.service
        service.stop_service()
        time.sleep(1)
        success, msg = service.start_service()
        severity = "success" if success else "warning"
        self.app.notify(f"Sistema reiniciado. {msg}", severity=severity)
        self._update_server_status()

    # ──────────────────────────────────────────────
    #  LOGS
    # ──────────────────────────────────────────────

    def _action_show_logs(self) -> None:
        """Exibe as últimas linhas do log do servidor."""
        log_section = self.query_one("#log-section")
        log_content = self.query_one("#settings-log-content", Static)

        log_file = "data/logs/server.log"
        if not os.path.exists(log_file):
            log_file = "video_tv.log"

        if not os.path.exists(log_file):
            log_content.update("[yellow]Nenhum arquivo de log encontrado.[/]")
        else:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    last_lines = "".join(lines[-40:])
                    log_content.update(last_lines)
            except Exception as e:
                log_content.update(f"[red]Erro ao ler log: {e}[/]")

        log_section.display = True

    # ──────────────────────────────────────────────
    #  DIAGNÓSTICO
    # ──────────────────────────────────────────────

    def _action_run_diagnostics(self) -> None:
        """Executa diagnóstico do sistema e exibe resultado."""
        from app.media_utils import MediaUtils
        scanner = MediaUtils()
        deps = scanner.check_dependencies()

        lines = ["[bold yellow]DIAGNÓSTICO DO SISTEMA[/]", ""]
        all_ok = True
        for name, info in deps.items():
            if info["ok"]:
                lines.append(f"[green]✔ {name.upper()}[/] — {info['version']}")
            else:
                lines.append(f"[red]✘ {name.upper()}[/] — {info['error']}")
                all_ok = False

        lines.append("")
        if all_ok:
            lines.append("[green]✔ Ambiente validado com sucesso.[/]")
        else:
            lines.append("[yellow]⚠ Existem problemas a serem resolvidos.[/]")

        log_section = self.query_one("#log-section")
        log_content = self.query_one("#settings-log-content", Static)
        log_content.update("\n".join(lines))
        log_section.display = True

    # ──────────────────────────────────────────────
    #  BACKUP DO BANCO
    # ──────────────────────────────────────────────

    def _action_backup_db(self) -> None:
        """Realiza backup do banco SQLite."""
        db_path = os.getenv("DATABASE_URL", "sqlite:///./video_tv.db")
        if db_path.startswith("sqlite:///"):
            db_file = db_path.replace("sqlite:///", "")

            if not os.path.exists(db_file):
                self.app.notify(f"Arquivo do banco não encontrado: {db_file}", severity="error")
                return

            backup_name = f"backup_videotv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            try:
                shutil.copy2(db_file, backup_name)
                self.app.notify(f"Backup concluído: {backup_name}", severity="success")
            except Exception as e:
                self.app.notify(f"Erro no backup: {e}", severity="error")
        else:
            self.app.notify("Banco de dados não é SQLite local.", severity="warning")

    # ──────────────────────────────────────────────
    #  MIGRAÇÃO/REPARO DO BANCO
    # ──────────────────────────────────────────────

    def _action_migrate_db(self) -> None:
        """Executa migração/reparo do banco de dados."""
        self.app.notify("Executando migração do banco de dados...", severity="info")
        try:
            success = DatabaseMigrator.migrate()
            if success:
                self.app.notify("Banco de dados atualizado com sucesso!", severity="success")
            else:
                self.app.notify("Erros durante a migração. Verifique os logs.", severity="error")
        except Exception as e:
            self.app.notify(f"Erro crítico na migração: {e}", severity="error")

