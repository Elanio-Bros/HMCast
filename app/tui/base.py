# Base de Menus da TUI

import os
import time
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm

console = Console()

class BaseMenu:
    label = "Menu Base"
    order = 99
    
    def __init__(self, db, scanner, service, page_size):
        self.db = db
        self.scanner = scanner
        self.service = service
        self.page_size = page_size

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def prompt_int_or_cancel(self, message: str, allow_zero: bool = False, allow_empty: bool = False):
        """Pede um inteiro. Retorna None se o usuário teclar V (Voltar) ou C (Cancelar). Se allow_empty=True, Enter vazio retorna ''."""
        while True:
            extra = " [bold white][V] Voltar[/]" if allow_zero else " [bold white][0 ou V] Voltar[/]"
            val_str = Prompt.ask(message + extra)
            v_lower = val_str.lower().strip()
            if v_lower in ['v', 'c']:
                return None
            if not allow_zero and v_lower == '0':
                return None
                
            if not val_str:
                if allow_empty:
                    return ""
                continue
                
            try:
                return int(val_str)
            except ValueError:
                console.print("[red]Digite um número válido (ou V para voltar).[/]")

    def browse_files(self, start_path=".", exts=None, dirs_only=False):
        """Navegador de Arquivos (TUI Visual)"""
        from rich.table import Table
        from rich.text import Text
        current_path = os.path.abspath(start_path)
        
        while True:
            self.clear_screen()
            console.print(f"[bold cyan]Navegador de Arquivos[/]")
            console.print(f"Diretório: [bold]{current_path}[/]\n")
            
            try:
                items = os.listdir(current_path)
            except Exception as e:
                console.print(f"[red]Erro ao ler pasta: {e}[/]")
                time.sleep(1.5)
                current_path = os.path.dirname(current_path)
                continue
                
            dirs = [".."]
            files = []
            
            for item in items:
                full_path = os.path.join(current_path, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                elif not dirs_only:
                    if not exts or any(item.lower().endswith(e) for e in exts):
                        files.append(item)
                        
            dirs.sort()
            files.sort()
            
            table = Table(box=None)
            table.add_column("ID", style="bold yellow")
            table.add_column("TIPO", style="dim")
            table.add_column("NOME")
            
            lookup = {}
            idx = 1
            for d in dirs:
                table.add_row(f"[{idx}]", "[DIR]", Text(d, style="blue" if d != ".." else "magenta"))
                lookup[idx] = (d, True)
                idx += 1
            
            for f in files:
                table.add_row(f"[{idx}]", "[FILE]", Text(f, style="green"))
                lookup[idx] = (f, False)
                idx += 1
                
            console.print(table)
            console.print("\n[bold white][V] Cancelar / Voltar[/]")
            if dirs_only:
                console.print("[bold yellow][S] SELECIONAR ESTE DIRETÓRIO[/]")
                
            opt = Prompt.ask("Escolha o número ou opção", default="v").lower()
            if opt in ['v', 'c']:
                return None
            if opt == 's' and dirs_only:
                return current_path
                
            try:
                n = int(opt)
                if n in lookup:
                    name, is_dir = lookup[n]
                    if name == "..":
                        current_path = os.path.dirname(current_path)
                    elif is_dir:
                        current_path = os.path.join(current_path, name)
                    else:
                        return os.path.join(current_path, name)
            except ValueError:
                pass

    def execute(self):
        raise NotImplementedError("O método execute deve ser implementado pela subclasse.")
