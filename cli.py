import os
import sys
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from rich.align import Align
from rich.text import Text

from database import SessionLocal
from models import Channels, Playlist, MediaItem, MediaFolder, ChannelSchedule
from media_utils import MediaUtils

console = Console()

class VideoTV_TUI:
    def __init__(self):
        self.db = SessionLocal()
        self.scanner = MediaUtils()
        self.running = True

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
        table = Table(show_header=False, box=box.SIMPLE, expand=True)
        table.add_row("[1] 📡 Gerenciar Canais")
        table.add_row("[2] 📝 Gerenciar Playlists")
        table.add_row("[3] 📅 Gerenciar Agenda")
        table.add_row("[4] 📂 Escanear Mídias")
        table.add_row("[5] 📊 Status do Sistema")
        table.add_row("[0] 🚪 Sair")
        return Panel(table, title="[bold yellow]MENU PRINCIPAL[/]", border_style="yellow", box=box.ROUNDED)

    def list_channels(self):
        channels = self.db.query(Channels).all()
        table = Table(title="CANAIS CONFIGURADOS", box=box.ROUNDED, header_style="bold cyan")
        table.add_column("ID", justify="center")
        table.add_column("NOME", style="bold")
        table.add_column("TIPO", justify="center")
        table.add_column("MODO", justify="center")
        table.add_column("DATA CRIAÇÃO", justify="right", style="dim")

        for c in channels:
            style = "green" if c.execution_mode == "ALWAYS_ON" else "blue"
            table.add_row(
                str(c.id),
                c.name,
                c.type,
                Text(c.execution_mode, style=style),
                c.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
        console.print("\n[bold cyan][A][/] Adicionar | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
        
        opt = Prompt.ask("Escolha uma opção", choices=["a", "e", "d", "v", "A", "E", "D", "V"], default="v").lower()
        if opt == "a":
            self.add_channel()
        elif opt == "d":
            self.delete_channel()
        elif opt == "e":
            self.edit_channel()

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
        playlists = self.db.query(Playlist).all()
        table = Table(title="PLAYLISTS DISPONÍVEIS", box=box.ROUNDED, header_style="bold magenta")
        table.add_column("ID", justify="center")
        table.add_column("NOME", style="bold")
        table.add_column("ORDEM", justify="center")

        for p in playlists:
            table.add_row(str(p.id), p.name, p.shuffle_mode or "SEQUENCIAL")
        
        console.print(table)
        console.print("\n[bold cyan][A][/] Criar | [bold yellow][I][/] Gerenciar Itens | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
        
        opt = Prompt.ask("Escolha uma opção", choices=["a", "i", "d", "v"], default="v").lower()
        if opt == "a":
            name = Prompt.ask("Nome da Playlist")
            p = Playlist(name=name)
            self.db.add(p)
            self.db.commit()
        elif opt == "i":
            self.manage_playlist_items()
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

        from models import PlaylistItem
        while True:
            self.clear_screen()
            console.print(Panel(Text(f"Gerenciando Itens: {p.name}", style="bold magenta")))
            
            items = self.db.query(PlaylistItem).filter(PlaylistItem.playlist_id == pid).order_by(PlaylistItem.order).all()
            table = Table(box=box.SIMPLE)
            table.add_column("ORDEM", justify="center")
            table.add_column("MÍDIA")
            
            for item in items:
                media = self.db.get(MediaItem, item.media_id)
                table.add_row(str(item.order), media.name if media else "N/A")
            
            console.print(table)
            console.print("\n[bold cyan][A][/] Adicionar Mídia | [bold red][D][/] Remover | [bold white][V][/] Voltar")
            
            opt = Prompt.ask("Opção", choices=["a", "d", "v"]).lower()
            if opt == "v": break
            if opt == "a":
                medias = self.db.query(MediaItem).limit(50).all()
                m_table = Table(title="Selecione a Mídia")
                m_table.add_column("ID")
                m_table.add_column("NOME")
                for m in medias: m_table.add_row(str(m.id), m.name)
                console.print(m_table)
                mid = IntPrompt.ask("ID da Mídia")
                order = IntPrompt.ask("Ordem", default=len(items) + 1)
                new_item = PlaylistItem(playlist_id=pid, media_id=mid, order=order)
                self.db.add(new_item)
                self.db.commit()
            if opt == "d":
                order = IntPrompt.ask("Ordem do item para remover")
                item = self.db.query(PlaylistItem).filter(PlaylistItem.playlist_id == pid, PlaylistItem.order == order).first()
                if item: self.db.delete(item); self.db.commit()

    def list_schedules(self):
        schedules = self.db.query(ChannelSchedule).all()
        table = Table(title="AGENDA DE TRANSMISSÃO", box=box.ROUNDED)
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
        console.print("\n[bold cyan][A][/] Adicionar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
        
        opt = Prompt.ask("Opção", choices=["a", "d", "v"]).lower()
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
        elif opt == "d":
            sid = IntPrompt.ask("ID do agendamento para deletar")
            s = self.db.get(ChannelSchedule, sid)
            if s: self.db.delete(s); self.db.commit()

    def scan_media(self):
        console.print("[bold yellow]Iniciando scan global de mídias...[/]")
        folders = self.db.query(MediaFolder).all()
        if not folders:
            console.print("[red]Nenhuma pasta de mídia cadastrada no banco![/]")
            path = Prompt.ask("Digite o caminho de uma pasta para cadastrar")
            if os.path.exists(path):
                f = MediaFolder(path=path, name=os.path.basename(path))
                self.db.add(f)
                self.db.commit()
                folders = [f]
        
        for f in folders:
            console.print(f"Lendo: {f.path}")
            self.scanner.scan_media_folder(f.id)
        
        console.print("[bold green]✔ Scan concluído![/]")
        time.sleep(2)

    def system_status(self):
        from engine import channel_runtimes
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

    def run(self):
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
                self.scan_media()
            elif choice == "5":
                self.system_status()
            elif choice == "0":
                self.running = False
            
        self.db.close()
        console.print("[bold blue]Até logo![/]")

if __name__ == "__main__":
    tui = VideoTV_TUI()
    tui.run()
