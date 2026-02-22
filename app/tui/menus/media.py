import time
import os
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from app.models import MediaItem, MediaFolder
from app.tui.base import BaseMenu, console

class MediaMenu(BaseMenu):
    label = "📂 Gerenciar Mídias"
    order = 4

    def execute(self):
        while True:
            self.clear_screen()
            console.print(Panel(Text("Gestão de Mídias e Conteúdo", style="bold green")))
            console.print("\n[1] 📋 Listar Mídias no Banco")
            console.print("[2] 📂 Gerenciar Pastas de Mídia")
            console.print("[3] ➕ Adicionar Arquivo Manualmente")
            console.print("[4] 🌍 Scan Global (Todas as Pastas)")
            console.print("[5] 🎯 Scan Específico (Escolher Pasta)")
            console.print("[bold white][V][/] 🔙 Voltar")
            
            opt = Prompt.ask("\nEscolha", choices=["1", "2", "3", "4", "5", "v"], default="v").lower()
            if opt == "v": break
            if opt == "1": self.list_media_items()
            if opt == "2": self.manage_media_folders()
            if opt == "3": self.add_media_manually()
            if opt == "4": self.scan_media()
            if opt == "5": self.scan_media(specific=True)

    def list_media_items(self):
        page = 0
        while True:
            self.clear_screen()
            total = self.db.query(MediaItem).count()
            total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1

            offset = page * self.page_size
            items = self.db.query(MediaItem).offset(offset).limit(self.page_size).all()
            
            table = Table(title=f"ITENS DE MÍDIA (Pág {page+1} de {total_pages})", box=box.SIMPLE)
            table.add_column("ID")
            table.add_column("NOME")
            table.add_column("DURAÇÃO (s)")
            
            for i in items:
                table.add_row(str(i.id), i.name, str(i.duration))
            
            console.print(table)
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold red][D][/] Deletar | [bold yellow][E][/] Editar Nome | [bold blue][M][/] Metadados | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "d", "e", "m", "v"]
            opt = Prompt.ask("Opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = IntPrompt.ask(f"Ir para página (1-{total_pages})", default=page+1)
                if 1 <= target <= total_pages: page = target - 1
            
            if opt == "d":
                mid = IntPrompt.ask("ID para deletar")
                item = self.db.get(MediaItem, mid)
                if item: self.db.delete(item); self.db.commit(); console.print("[red]Removido.[/]"); time.sleep(1)
            elif opt == "e":
                mid = IntPrompt.ask("ID para editar")
                item = self.db.get(MediaItem, mid)
                if item:
                    item.name = Prompt.ask("Novo Nome", default=item.name)
                    self.db.commit(); console.print("[green]Atualizado.[/]"); time.sleep(1)
            elif opt == "m":
                self.edit_media_metadata()

    def edit_media_metadata(self):
        mid = IntPrompt.ask("ID da Mídia")
        item = self.db.get(MediaItem, mid)
        if not item: return

        skips = item.skips or {}
        
        while True:
            self.clear_screen()
            console.print(Panel(Text(f"Metadados de Corte: {item.name}", style="bold green")))
            
            intro = skips.get("intro", {"start": "00:00:00", "end": "00:00:00"})
            finish = skips.get("finish", {"start": "-00:00:00", "end": "-00:00:00"})
            cuts = skips.get("cuts", [])
            
            console.print(f"[cyan]1.[/] Pular Abertura (Intro): [yellow]{intro['start']} -> {intro['end']}[/]")
            console.print(f"[cyan]2.[/] Pular Créditos/Fim (Finish): [yellow]Inicia em {finish['start']}[/]")
            console.print(f"[cyan]3.[/] Cortes Manuais (Cuts): [yellow]{len(cuts)} cortes configurados[/]")
            console.print("[bold white][V][/]. Salvar e Voltar")

            opt = Prompt.ask("\nEscolha", choices=["1", "2", "3", "v"], default="v").lower()
            if opt == "v":
                item.skips = skips
                self.db.commit()
                break
            
            if opt == "1":
                intro["start"] = Prompt.ask("Início do Pulo (HH:MM:SS)", default=intro["start"])
                intro["end"] = Prompt.ask("Fim do Pulo (HH:MM:SS)", default=intro["end"])
                skips["intro"] = intro
            
            if opt == "2":
                finish["start"] = Prompt.ask("Início do Pulo (HH:MM:SS ou -segundos)", default=finish["start"])
                finish["end"] = "-00:00:00"
                skips["finish"] = finish
                
            if opt == "3":
                console.print("\n[1] Adicionar Corte | [2] Limpar Cortes | [V] Voltar")
                copt = Prompt.ask("Escolha", choices=["1", "2", "v"], default="v").lower()
                if copt == "1":
                    c_start = Prompt.ask("Início do Corte (HH:MM:SS)")
                    c_end = Prompt.ask("Fim do Corte (HH:MM:SS)")
                    cuts.append({"start": c_start, "end": c_end})
                    skips["cuts"] = cuts
                elif copt == "2":
                    skips["cuts"] = []

    def manage_media_folders(self):
        while True:
            self.clear_screen()
            folders = self.db.query(MediaFolder).all()
            table = Table(title="PASTAS DE MÍDIA")
            table.add_column("ID")
            table.add_column("NOME")
            table.add_column("CAMINHO")
            
            for f in folders:
                table.add_row(str(f.id), f.name, f.path)
            
            console.print(table)
            console.print("\n[bold cyan][A][/] Adicionar | [bold yellow][E][/] Editar | [bold red][D][/] Remover | [bold white][V][/] Voltar")
            opt = Prompt.ask("Opção", choices=["a", "e", "d", "v"], default="v").lower()
            
            if opt == "v": break
            if opt == "a":
                path = Prompt.ask("Caminho da Pasta")
                if os.path.exists(path):
                    name = Prompt.ask("Nome da Pasta", default=os.path.basename(path))
                    f = MediaFolder(path=path, name=name)
                    self.db.add(f); self.db.commit()
            elif opt == "e":
                fid = IntPrompt.ask("ID para editar")
                f = self.db.get(MediaFolder, fid)
                if f:
                    f.name = Prompt.ask("Novo Nome", default=f.name)
                    f.path = Prompt.ask("Novo Caminho", default=f.path)
                    self.db.commit(); console.print("[green]Atualizado.[/]"); time.sleep(1)
            elif opt == "d":
                fid = IntPrompt.ask("ID para remover")
                f = self.db.get(MediaFolder, fid)
                if f: self.db.delete(f); self.db.commit()

    def scan_media(self, specific=False):
        if specific:
            folders = self.db.query(MediaFolder).all()
            if not folders:
                console.print("[yellow]Nenhuma pasta cadastrada.[/]")
                time.sleep(1)
                return
            
            table = Table(title="Selecione a Pasta para Scan")
            table.add_column("ID")
            table.add_column("NOME")
            for f in folders: table.add_row(str(f.id), f.name)
            console.print(table)
            
            fid = IntPrompt.ask("ID da Pasta")
            folder = self.db.get(MediaFolder, fid)
            if folder:
                console.print(f"[bold yellow]Escaneando pasta: {folder.name}...[/]")
                self.scanner.scan_media_folder(folder.path)
                console.print("[bold green]✔ Scan concluído![/]")
            else:
                console.print("[red]Pasta não encontrada.[/]")
        else:
            console.print("[bold yellow]Iniciando scan global de mídias...[/]")
            folders = self.db.query(MediaFolder).all()
            for f in folders:
                console.print(f"Lendo: {f.path}")
                self.scanner.scan_media_folder(f.path)
            console.print("[bold green]✔ Scan concluído![/]")
        time.sleep(1.5)

    def add_media_manually(self):
        path = Prompt.ask("Caminho do arquivo (Vídeo/Áudio)")
        if not os.path.exists(path):
            console.print("[bold red]✘ Arquivo não encontrado![/]")
            time.sleep(1.5)
            return

        exists = self.db.query(MediaItem).filter(MediaItem.file == path).first()
        if exists:
            console.print(f"[yellow]⚠ Este arquivo já está registrado como ID: {exists.id}[/]")
            time.sleep(1.5)
            return

        console.print("[yellow]Analisando metadados...[/]")
        duration = self.scanner.get_media_duration(path)
        if duration <= 0:
            console.print("[bold red]✘ Não foi possível obter a duração do arquivo.[/]")
            time.sleep(1.5)
            return

        name = Prompt.ask("Nome de exibição", default=os.path.basename(path))
        new_item = MediaItem(name=name, file=path, duration=duration, folder_id=None)
        self.db.add(new_item)
        self.db.commit()
        console.print(f"[bold green]✔ Mídia adicionada com sucesso! (ID: {new_item.id})[/]")
        time.sleep(2)
