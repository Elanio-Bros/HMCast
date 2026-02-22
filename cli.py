import os
import sys
import time
import socket
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from rich.align import Align
from rich.text import Text

from app.database import engine, SessionLocal
from app.models import Base, Channels, Playlist, MediaItem, MediaFolder, ChannelSchedule, PlaylistItem
from app.media_utils import MediaUtils
from app.engine import channel_runtimes
from app.service_manager import ServiceManager


console = Console()
load_dotenv()

class TUI:
    def __init__(self):
        Base.metadata.create_all(bind=engine)
        
        self.db = SessionLocal()
        self.scanner = MediaUtils()
        self.service = ServiceManager()
        self.running = True
        self.page_size = int(os.getenv("CLI_PAGE_SIZE", 10))

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
        table.add_row("[1] 📡 Gerenciar Canais")
        table.add_row("[2] 📝 Gerenciar Playlists")
        table.add_row("[3] 📅 Gerenciar Agenda")
        table.add_row("[4] 📂 Gerenciar Mídias")
        table.add_row("[5] ⚙️ Gerenciar Servidor")
        table.add_row("[0] 🚪 Sair")
        return Panel(table, title="[bold yellow]MENU PRINCIPAL[/]", border_style="yellow", box=box.ROUNDED)

    def list_channels(self):
        page = 0
        while True:
            self.clear_screen()
            total = self.db.query(Channels).count()
            total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
            
            offset = page * self.page_size
            channels = self.db.query(Channels).offset(offset).limit(self.page_size).all()
            
            table = Table(title=f"CANAIS CONFIGURADOS (Pág {page+1} de {total_pages})", box=box.ROUNDED, header_style="bold cyan")
            table.add_column("ID", justify="center")
            table.add_column("NOME", style="bold")
            table.add_column("TIPO", justify="center")
            table.add_column("MODO", justify="center")

            for c in channels:
                style = "green" if c.execution_mode == "ALWAYS_ON" else "blue"
                table.add_row(str(c.id), c.name, c.type, Text(c.execution_mode, style=style))
            
            console.print(table)
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold cyan][A][/] Adicionar | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "a", "e", "d", "v"]
            opt = Prompt.ask("Opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = IntPrompt.ask(f"Ir para página (1-{total_pages})", default=page+1)
                if 1 <= target <= total_pages: page = target - 1
            if opt == "a": self.add_channel()
            elif opt == "e": self.edit_channel()
            elif opt == "d": self.delete_channel()

    def add_channel(self):
        name = Prompt.ask("Nome do Canal")
        ctype = Prompt.ask("Tipo", choices=["TV", "RADIO"], default="TV")
        mode = Prompt.ask("Modo de Execução", choices=["ALWAYS_ON", "ON_DEMAND", "PREDICTIVE"], default="ON_DEMAND")
        
        new_ch = Channels(name=name, type=ctype, execution_mode=mode)
        self.db.add(new_ch)
        self.db.commit()
        console.print("[bold green]✔ Canal criado com sucesso![/]")
        time.sleep(1)

    def delete_channel(self):
        cid = IntPrompt.ask("ID do Canal para deletar")
        ch = self.db.get(Channels, cid)
        if ch and Confirm.ask(f"Tem certeza que deseja deletar o canal '{ch.name}'?"):
            self.db.delete(ch)
            self.db.commit()
            console.print("[bold red]✘ Canal removido.[/]")
            time.sleep(1)

    def edit_channel(self):
        cid = IntPrompt.ask("ID do Canal para editar")
        ch = self.db.get(Channels, cid)
        if ch:
            ch.name = Prompt.ask("Novo Nome", default=ch.name)
            ch.type = Prompt.ask("Novo Tipo", choices=["TV", "RADIO"], default=ch.type)
            ch.execution_mode = Prompt.ask("Novo Modo", choices=["ALWAYS_ON", "ON_DEMAND", "PREDICTIVE"], default=ch.execution_mode)
            self.db.commit()
            console.print("[bold green]✔ Canal atualizado![/]")
            time.sleep(1)

    def list_playlists(self):
        page = 0
        while True:
            self.clear_screen()
            total = self.db.query(Playlist).count()
            total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
            
            offset = page * self.page_size
            playlists = self.db.query(Playlist).offset(offset).limit(self.page_size).all()

            table = Table(title=f"PLAYLISTS DISPONÍVEIS (Pág {page+1} de {total_pages})", box=box.ROUNDED, header_style="bold magenta")
            table.add_column("ID", justify="center")
            table.add_column("NOME", style="bold")
            table.add_column("MODO", justify="center")

            for p in playlists:
                table.add_row(str(p.id), p.name, p.shuffle_mode or "SEQUENCIAL")
            
            console.print(table)
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold cyan][A][/] Criar | [bold yellow][I][/] Itens | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "a", "i", "e", "d", "v"]
            opt = Prompt.ask("Escolha uma opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = IntPrompt.ask(f"Ir para página (1-{total_pages})", default=page+1)
                if 1 <= target <= total_pages: page = target - 1
            if opt == "a":
                name = Prompt.ask("Nome da Playlist")
                p = Playlist(name=name)
                self.db.add(p)
                self.db.commit()
            elif opt == "i":
                self.manage_playlist_items()
            elif opt == "e":
                pid = IntPrompt.ask("ID da Playlist para editar")
                p = self.db.get(Playlist, pid)
                if p:
                    p.name = Prompt.ask("Novo Nome", default=p.name)
                    p.shuffle_mode = Prompt.ask("Modo Shuffle", choices=["SEQUENCIAL", "SHUFFLE"], default=p.shuffle_mode or "SEQUENCIAL")
                    self.db.commit(); console.print("[green]Atualizada.[/]"); time.sleep(1)
            elif opt == "d":
                pid = IntPrompt.ask("ID para deletar")
                p = self.db.get(Playlist, pid)
                if p: 
                    self.db.delete(p)
                    self.db.commit()
                    console.print("[bold red]✘ Playlist removida.[/]")
                    time.sleep(1)

    def manage_playlist_items(self):
        pid = IntPrompt.ask("ID da Playlist para gerenciar")
        p = self.db.get(Playlist, pid)
        if not p: return

        while True:
            self.clear_screen()
            console.print(Panel(Text(f"Gerenciando Itens: {p.name}", style="bold magenta")))
            
            items = self.db.query(PlaylistItem).filter(PlaylistItem.playlist_id == pid).order_by(PlaylistItem.order).all()
            table = Table(box=box.SIMPLE)
            table.add_column("PAPEL")
            table.add_column("MÍDIA")
            
            for item in items:
                media = self.db.get(MediaItem, item.media_id)
                role_style = "cyan" if item.role == "OPENING" else "yellow" if item.role == "CLOSING" else "white"
                table.add_row(str(item.order), f"[{role_style}]{item.role}[/]", media.name if media else "N/A")
            
            console.print(table)
            console.print("\n[bold cyan][A][/] Adicionar Mídia | [bold red][D][/] Remover | [bold white][V][/] Voltar")
            
            opt = Prompt.ask("Opção", choices=["a", "d", "v"]).lower()
            if opt == "v": break
            if opt == "a":
                m_page = 0
                while True:
                    self.clear_screen()
                    m_total = self.db.query(MediaItem).count()
                    m_total_pages = (m_total + self.page_size - 1) // self.page_size if m_total > 0 else 1
                    
                    m_offset = m_page * self.page_size
                    medias = self.db.query(MediaItem).offset(m_offset).limit(self.page_size).all()
                    
                    m_table = Table(title=f"Selecione a Mídia (Pág {m_page+1} de {m_total_pages})")
                    m_table.add_column("ID")
                    m_table.add_column("NOME")
                    for m in medias: m_table.add_row(str(m.id), m.name)
                    console.print(m_table)
                    
                    console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold white][V][/] Voltar")
                    m_opt = Prompt.ask("Escolha o ID da Mídia ou Opção", default="v")
                    
                    if m_opt.lower() == "v": break
                    if m_opt.lower() == "n": m_page = (m_page + 1) % m_total_pages; continue
                    if m_opt.lower() == "p": m_page = (m_page - 1) % m_total_pages; continue
                    if m_opt.lower() == "g":
                        m_target = IntPrompt.ask(f"Ir para página (1-{m_total_pages})", default=m_page+1)
                        if 1 <= m_target <= m_total_pages: m_page = m_target - 1
                        continue
                    
                    try:
                        mid = int(m_opt)
                        media = self.db.get(MediaItem, mid)
                        if media:
                            order = IntPrompt.ask("Ordem", default=len(items) + 1)
                            role = Prompt.ask("Papel", choices=["OPENING", "CONTENT", "CLOSING"], default="CONTENT")
                            new_item = PlaylistItem(playlist_id=pid, media_id=mid, order=order, role=role)
                            self.db.add(new_item)
                            self.db.commit()
                            break
                    except:
                        console.print("[red]ID inválido.[/]")
                        time.sleep(1)
            if opt == "d":
                order = IntPrompt.ask("Ordem do item para remover")
                item = self.db.query(PlaylistItem).filter(PlaylistItem.playlist_id == pid, PlaylistItem.order == order).first()
                if item: self.db.delete(item); self.db.commit()


    def list_schedules(self):
        page = 0
        while True:
            self.clear_screen()
            total = self.db.query(ChannelSchedule).count()
            total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1

            offset = page * self.page_size
            schedules = self.db.query(ChannelSchedule).offset(offset).limit(self.page_size).all()
            
            table = Table(title=f"AGENDA DE TRANSMISSÃO (Pág {page+1} de {total_pages})", box=box.ROUNDED)
            table.add_column("ID")
            table.add_column("CANAL")
            table.add_column("PLAYLIST")
            table.add_column("INÍCIO")
            table.add_column("FIM")

            for s in schedules:
                ch = self.db.get(Channels, s.channel_id)
                pl = self.db.get(Playlist, s.playlist_id)
                table.add_row(
                    str(s.id),
                    ch.name if ch else "N/A",
                    pl.name if pl else "N/A",
                    s.start_time.strftime("%H:%M"),
                    s.end_time.strftime("%H:%M")
                )
            
            console.print(table)
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold cyan][A][/] Adicionar | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "a", "e", "d", "v"]
            opt = Prompt.ask("Opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = IntPrompt.ask(f"Ir para página (1-{total_pages})", default=page+1)
                if 1 <= target <= total_pages: page = target - 1
            if opt == "a":
                cid = IntPrompt.ask("ID do Canal")
                pid = IntPrompt.ask("ID da Playlist")
                start = Prompt.ask("Início (HH:MM)")
                end = Prompt.ask("Fim (HH:MM)")
                
                st = datetime.strptime(start, "%H:%M").time()
                et = datetime.strptime(end, "%H:%M").time()
                
                sched = ChannelSchedule(channel_id=cid, playlist_id=pid, start_time=st, end_time=et)
                self.db.add(sched)
                self.db.commit()
                console.print("[bold green]✔ Agendamento criado![/]")
                time.sleep(1)
            elif opt == "e":
                sid = IntPrompt.ask("ID do agendamento para editar")
                s = self.db.get(ChannelSchedule, sid)
                if s:
                    s.channel_id = IntPrompt.ask("Novo ID do Canal", default=s.channel_id)
                    s.playlist_id = IntPrompt.ask("Novo ID da Playlist", default=s.playlist_id)
                    st_str = Prompt.ask("Novo Início (HH:MM)", default=s.start_time.strftime("%H:%M"))
                    et_str = Prompt.ask("Novo Fim (HH:MM)", default=s.end_time.strftime("%H:%M"))
                    s.start_time = datetime.strptime(st_str, "%H:%M").time()
                    s.end_time = datetime.strptime(et_str, "%H:%M").time()
                    self.db.commit(); console.print("[green]Agendamento atualizado![/]"); time.sleep(1)
            elif opt == "d":
                sid = IntPrompt.ask("ID do agendamento para deletar")
                s = self.db.get(ChannelSchedule, sid)
                if s: self.db.delete(s); self.db.commit()

    def manage_media(self):
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
                finish["end"] = "-00:00:00" # Geralmente até o fim
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

        # Verifica se já existe
        exists = self.db.query(MediaItem).filter(MediaItem.file == path).first()
        if exists:
            console.print(f"[yellow]⚠ Este arquivo já está registrado como ID: {exists.id}[/]")
            time.sleep(1.5)
            return

        console.print("[yellow]Analisando metadados...[/]")
        duration = self.scanner.get_duration(path)
        if duration <= 0:
            console.print("[bold red]✘ Não foi possível obter a duração do arquivo.[/]")
            time.sleep(1.5)
            return

        name = Prompt.ask("Nome de exibição", default=os.path.basename(path))
        new_item = MediaItem(
            name=name,
            file=path,
            duration=duration,
            folder_id=None # Independente de pasta monitorada
        )
        self.db.add(new_item)
        self.db.commit()
        console.print(f"[bold green]✔ Mídia adicionada com sucesso! (ID: {new_item.id})[/]")
        time.sleep(2)

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

    def is_server_running(self):
        return self.service.is_running()

    def manage_server(self):
        while True:
            self.clear_screen()
            running = self.is_server_running()
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
        
        # Futuras validações podem entrar aqui (espaço, banco, etc)
        console.print("\n[dim]Ambiente de transmissão validado.[/]")
        Prompt.ask("\nPressione Enter para voltar")

    def start_api_server(self):
        console.print("[bold yellow]Iniciando Servidor API (Uvicorn)...[/]")
        try:
            # Pegamos o valor da flag para evitar erro de lint em ambientes non-windows
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
        if not self.is_server_running():
            console.print("[yellow]ℹ O servidor já parece estar desligado.[/]")
            time.sleep(1)
            return

        console.print("[bold red]Desligando Servidor API...[/]")
        try:
            if os.name == 'nt':
                # No Windows, usamos taskkill buscando pelo uvicorn ou pela porta 8000
                # O comando abaixo busca o PID da porta 8000 e mata
                cmd = 'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :8000\') do taskkill /f /pid %a'
                subprocess.run(cmd, shell=True, capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
            console.print("[bold green]✔ Comando de desligamento enviado![/]")
        except Exception as e:
            console.print(f"[bold red]✘ Erro ao desligar: {e}[/]")
        time.sleep(1.5)

    def run(self):
        # 🛡️ Portão de Segurança: Validação de Dependências antes do Loop
        deps = self.scanner.check_dependencies()
        all_ok = all(info["ok"] for info in deps.values())
        
        if not all_ok:
            self.clear_screen()
            console.print(self.make_header())
            table = Table(title="[bold red]ERRO CRÍTICO DE AMBIENTE[/]", box=box.DOUBLE_EDGE, border_style="red")
            table.add_column("DEPENDÊNCIA", style="bold")
            table.add_column("STATUS")
            table.add_column("DETALHES")
            
            for name, info in deps.items():
                status = "[green]OK[/]" if info["ok"] else "[red]FALHA[/]"
                err = "" if info["ok"] else info["error"]
                table.add_row(name.upper(), status, err)
            
            console.print(table)
            console.print("\n[bold yellow]O sistema não pode prosseguir sem estas dependências essenciais.[/]")
            console.print("[dim]Dica: Verifique se o FFMPEG e FFPROBE estão no PATH ou configurados corretamente no seu arquivo .env[/]\n")
            
            # Força o usuário a sair ou tentar novamente (reiniciando a TUI)
            Prompt.ask("[bold white][0][/] Sair", choices=["0"], default="0")
            self.running = False

        while self.running:
            self.clear_screen()
            console.print(self.make_header())
            console.print(self.draw_menu())
            
            choice = Prompt.ask("Selecione", choices=["1", "2", "3", "4", "5", "0"], default="0")
            
            if choice == "1":
                self.list_channels()
            elif choice == "2":
                self.list_playlists()
            elif choice == "3":
                self.list_schedules()
            elif choice == "4":
                self.manage_media()
            elif choice == "5":
                self.manage_server()
            elif choice == "0":
                self.running = False
            
        self.db.close()
        console.print("[bold blue]Até logo![/]")

if __name__ == "__main__":
    tui = TUI()
    tui.run()
