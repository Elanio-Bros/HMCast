import time
import os
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from app.engine import channel_runtimes
from app.tui.base import BaseMenu, console
from app.migrations import DatabaseMigrator

class ServerMenu(BaseMenu):
    label = "Gerenciar Servidor"
    order = 5

    def execute(self):
        while True:
            self.clear_screen()
            running = self.service.is_running()
            status = f"[green]{self.service.get_status()}[/]" if running else f"[red]{self.service.get_status()}[/]"
            
            console.print(Panel(Text(f"Gestão do Servidor - Status: {status}", style="bold cyan")))
            console.print(" [bold cyan][1]🚀 Iniciar Transmissão")
            console.print(" [bold cyan][2] 🛑 Parar Transmissão")
            console.print(" [bold cyan][3] 🔄 Reiniciar Transmissão")
            console.print(" [bold cyan][4] 📄 Ver Logs")
            console.print(" [bold cyan][5] 📊 Status Detalhado")
            console.print(" [bold cyan][6] 🩺 Validar Ambiente")
            console.print(" [bold yellow][7] 🩹 Reparar/Migrar Banco de Dados")
            console.print(" [bold cyan][8] 📡 Logs ao Vivo (Live Tail)")
            console.print(" [bold green][9] 💾 Backup do Banco de Dados")
            console.print(" [bold white][V] Voltar")

            opt = Prompt.ask("\nEscolha uma opção", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "v"], default="v").lower()

            if opt == "v": break
            elif opt == "1":
                success, msg = self.service.start_service()
                if success: console.print(f"[bold green]✔ {msg}[/]")
                else: console.print(f"[bold yellow]⚠ {msg}[/]")
                time.sleep(1.5)
            elif opt == "2":
                success, msg = self.service.stop_service()
                if success: console.print(f"[bold red]✔ {msg}[/]")
                else: console.print(f"[bold yellow]⚠ {msg}[/]")
                time.sleep(1.5)
            elif opt == "3":
                self.service.stop_service()
                time.sleep(1)
                self.service.start_service()
                console.print("[bold green]✔ Sistema reiniciado.[/]")
                time.sleep(1.5)
            elif opt == "4":
                self.clear_screen()
                console.print(Panel(self.service.get_logs(), title="LOGS DO SERVIDOR", border_style="dim"))
                Prompt.ask("\nPressione Enter para voltar")
            elif opt == "5":
                self.system_status()
            elif opt == "6":
                self.run_system_diagnostics()
            elif opt == "7":
                self.run_migration()
            elif opt == "8":
                self.live_logs()
            elif opt == "9":
                self.backup_db()

    def system_status(self):
        table = Table(title="STATUS DO MOTOR (ENGINE)", box=box.DOUBLE_EDGE)
        table.add_column("CANAL", style="bold")
        table.add_column("STATUS", justify="center")
        table.add_column("PROCESSO", justify="center")

        for cid, runtime in channel_runtimes.items():
            status = "[green]ATIVO[/]" if runtime.running else "[red]PARADO[/]"
            proc = "[green]FFMPEG RODANDO[/]" if (runtime.player.process and runtime.player.process.poll() is None) else "[dim]OFFLINE[/]"
            table.add_row(f"Canal {cid}", status, proc)
        
        console.print(table)
        Prompt.ask("\nPressione Enter para voltar")

    def run_system_diagnostics(self):
        self.clear_screen()
        console.print(Panel(Text("Diagnóstico do Sistema", style="bold yellow")))
        console.print("[yellow]Validando dependências...[/]\n")
        
        deps = self.scanner.check_dependencies()
        table = Table(box=box.SIMPLE)
        table.add_column("COMPONENTE")
        table.add_column("STATUS")
        table.add_column("DETALHES")
        
        for name, info in deps.items():
            if info["ok"]:
                table.add_row(name.upper(), "[bold green]✔ OK[/]", info["version"])
            else:
                table.add_row(name.upper(), "[bold red]✘ FALHA[/]", f"[red]{info['error']}[/]")
        
        console.print(table)
        console.print("\n[dim]Ambiente de transmissão validado.[/]")
        Prompt.ask("\nPressione Enter para voltar")

    def run_migration(self):
        console.print("[bold yellow]Iniciando reparo/migração do banco de dados...[/]")
        try:
            success = DatabaseMigrator.migrate()
            if success:
                console.print("[bold green]✔ Banco de dados atualizado com sucesso![/]")
            else:
                console.print("[bold red]✘ Ocorreram erros durante a migração. Verifique os logs.[/]")
        except Exception as e:
            console.print(f"[bold red]✘ Erro crítico na migração: {e}[/]")
        
        Prompt.ask("\nPressione Enter para continuar")

    def live_logs(self):
        self.clear_screen()
        console.print(Panel(Text("Monitor Live: (Pressione Ctrl+C para sair)", style="bold cyan")))
        
        log_file = "video_tv.log"
        if not os.path.exists(log_file):
            console.print(f"[yellow]Arquivo de log ({log_file}) não encontrado.[/]")
            Prompt.ask("\nPressione Enter para voltar")
            return
            
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    console.print(line.rstrip(), highlight=False)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            console.print(f"[red]Erro no live log: {e}[/]")
            time.sleep(2)

    def backup_db(self):
        import shutil
        from datetime import datetime
        
        self.clear_screen()
        console.print(Panel(Text("Backup do Banco de Dados SQLite", style="bold green")))
        
        db_path = os.getenv("DATABASE_URL", "sqlite:///./video_tv.db")
        if db_path.startswith("sqlite:///"):
            db_file = db_path.replace("sqlite:///", "")
            
            if not os.path.exists(db_file):
                console.print(f"[red]Arquivo do banco não encontrado em: {db_file}[/]")
            else:
                backup_name = f"backup_videotv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                try:
                    shutil.copy2(db_file, backup_name)
                    console.print(f"[bold green]✔ Backup concluído com sucesso![/]")
                    console.print(f"[cyan]Arquivo gerado na raiz: {backup_name}[/]")
                except Exception as e:
                    console.print(f"[bold red]✘ Erro ao fazer backup: {e}[/]")
        else:
            console.print("[yellow]O banco de dados atual não é um SQLite local reconhecido.[/]")
            
        Prompt.ask("\nPressione Enter para voltar")
