from rich.table import Table
import os
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
import time
from app.engine import channel_runtimes
from app.tui.base import BaseMenu, console

class ServerMenu(BaseMenu):
    label = "⚙️ Gerenciar Servidor"
    order = 5

    def execute(self):
        while True:
            self.clear_screen()
            running = self.service.is_running()
            status = f"[green]{self.service.get_status()}[/]" if running else f"[red]{self.service.get_status()}[/]"
            
            console.print(Panel(Text(f"Gestão do Servidor - Status: {status}", style="bold cyan")))
            console.print("\n[1] 🚀 Iniciar Servidor (Background)")
            console.print("[2] 🛑 Desligar Servidor")
            console.print("[3] 🔄 Reiniciar")
            console.print("[4] 📄 Ver Logs (Últimas 20 linhas)")
            console.print("[5] 📊 Status Detalhado (Engine)")
            console.print("[6] 🩺 Diagnóstico do Sistema")
            console.print("[bold white][V][/] 🔙 Voltar")
            
            opt = Prompt.ask("\nEscolha", choices=["1", "2", "3", "4", "5", "6", "v"], default="v").lower()
            if opt == "v": break
            
            if opt == "1":
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

    def start_api_server(self):
        import sys
        import subprocess
        console.print("[bold yellow]Iniciando Servidor API (Uvicorn)...[/]")
        try:
            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"],
                creationflags=CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            console.print("[bold green]✔ Servidor API disparado em uma nova janela![/]")
        except Exception as e:
            console.print(f"[bold red]✘ Erro ao iniciar servidor: {e}[/]")
        time.sleep(1.5)

    def stop_api_server(self):
        import subprocess
        if not self.service.is_running():
            console.print("[yellow]ℹ O servidor já parece estar desligado.[/]")
            time.sleep(1)
            return

        console.print("[bold red]Desligando Servidor API...[/]")
        try:
            if os.name == 'nt':
                cmd = 'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :8000\') do taskkill /f /pid %a'
                subprocess.run(cmd, shell=True, capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
            console.print("[bold green]✔ Comando de desligamento enviado![/]")
        except Exception as e:
            console.print(f"[bold red]✘ Erro ao desligar: {e}[/]")
        time.sleep(1.5)
