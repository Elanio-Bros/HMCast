import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from rich.text import Text

from app.database import engine, SessionLocal
from app.models import Base
from app.media_utils import MediaUtils
from app.service_manager import ServiceManager

# Importação da base e dos menus
from app.tui.base import console
from app.tui.menus.channels import ChannelsMenu
from app.tui.menus.playlists import PlaylistsMenu
from app.tui.menus.media import MediaMenu
from app.tui.menus.server import ServerMenu

load_dotenv()

class TUI:
    def __init__(self):
        # Garante que as tabelas existam
        Base.metadata.create_all(bind=engine)
        
        self.db = SessionLocal()
        self.scanner = MediaUtils()
        self.service = ServiceManager()
        self.running = True
        self.page_size = int(os.getenv("CLI_PAGE_SIZE", 10))
        
        # Inicializa os módulos de menu
        self.menus = [
            ChannelsMenu(self.db, self.scanner, self.service, self.page_size),
            PlaylistsMenu(self.db, self.scanner, self.service, self.page_size),
            MediaMenu(self.db, self.scanner, self.service, self.page_size),
            ServerMenu(self.db, self.scanner, self.service, self.page_size),
        ]
        # Ordenação garantida pela propriedade 'order' de cada classe
        self.menus.sort(key=lambda m: m.order)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def make_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            Text("📺 VIDEO TV - GESTÃO ENTERPRISE", style="bold magenta"),
            Text(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), style="dim white"),
        )
        return Panel(grid, style="bold blue", box=box.ROUNDED)

    def draw_menu(self):
        table = Table(show_header=False, box=box.SIMPLE)
        # Monta o menu dinamicamente baseado nos módulos carregados
        for i, menu in enumerate(self.menus, 1):
            table.add_row(f"[{i}] {menu.label}")
        
        table.add_row("[0] 🚪 Sair")
        return Panel(table, title="[bold yellow]MENU PRINCIPAL[/]", border_style="yellow", box=box.ROUNDED)

    def run(self):
        while self.running:
            self.clear_screen()
            console.print(self.make_header())
            console.print(self.draw_menu())
            
            # Gera as opções válidas dinamicamente
            choices = [str(i) for i in range(len(self.menus) + 1)]
            opt = Prompt.ask("\nEscolha uma opção", choices=choices, default="0")
            
            if opt == "0":
                console.print("[yellow]Saindo...[/]")
                self.running = False
                break
            
            try:
                idx = int(opt) - 1
                if 0 <= idx < len(self.menus):
                    self.menus[idx].execute()
            except Exception as e:
                console.print(f"[bold red]Ocorreu um erro inesperado: {e}[/]")
                time.sleep(2)

if __name__ == "__main__":
    # Inicia a aplicação
    tui = TUI()
    try:
        tui.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompido pelo usuário. Saindo...[/]")
        sys.exit(0)
