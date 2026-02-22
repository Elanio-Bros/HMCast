from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
import time
from app.models import Playlist, MediaItem, PlaylistItem
from app.tui.base import BaseMenu, console

class PlaylistsMenu(BaseMenu):
    label = "📝 Gerenciar Playlists"
    order = 2

    def execute(self):
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
            
            if opt == "a": self.create_playlist()
            elif opt == "i": self.manage_playlist_items()
            elif opt == "e": self.edit_playlist()
            elif opt == "d": self.delete_playlist()

    def create_playlist(self):
        name = Prompt.ask("Nome da Playlist")
        p = Playlist(name=name)
        self.db.add(p)
        self.db.commit()
        console.print("[green]Playlist criada![/]")
        time.sleep(1)

    def edit_playlist(self):
        pid = IntPrompt.ask("ID da Playlist para editar")
        p = self.db.get(Playlist, pid)
        if p:
            p.name = Prompt.ask("Novo Nome", default=p.name)
            p.shuffle_mode = Prompt.ask("Modo Shuffle", choices=["SEQUENCIAL", "SHUFFLE"], default=p.shuffle_mode or "SEQUENCIAL")
            self.db.commit(); console.print("[green]Atualizada.[/]"); time.sleep(1)

    def delete_playlist(self):
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
            table.add_column("ORDEM")
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
