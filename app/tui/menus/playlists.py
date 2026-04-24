import time
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from app.models import Playlist, MediaItem, PlaylistItem
from app.tui.base import BaseMenu, console

class PlaylistsMenu(BaseMenu):
    label = "Gerenciar Playlists"
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
                mode_str = "SHUFFLE" if p.shuffle else "SEQUENCIAL"
                table.add_row(str(p.id), p.name, mode_str)
            
            console.print(table)
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold cyan][A][/] Criar | [bold yellow][I][/] Itens | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "a", "i", "e", "d", "v"]
            opt = Prompt.ask("Escolha uma opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = self.prompt_int_or_cancel(f"Ir para página (1-{total_pages})", allow_zero=True)
                if target is not None and 1 <= target <= total_pages: page = target - 1
            
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
        pid = self.prompt_int_or_cancel("ID da Playlist para editar")
        if pid is None: return
        p = self.db.get(Playlist, pid)
        if p:
            p.name = Prompt.ask("Novo Nome", default=p.name)
            mode = Prompt.ask("Modo Shuffle", choices=["SEQUENCIAL", "SHUFFLE"], default="SHUFFLE" if p.shuffle else "SEQUENCIAL")
            p.shuffle = (mode == "SHUFFLE")
            self.db.commit(); console.print("[green]Atualizada.[/]"); time.sleep(1)

    def delete_playlist(self):
        pid = self.prompt_int_or_cancel("ID para deletar")
        if pid is None: return
        p = self.db.get(Playlist, pid)
        if p: 
            self.db.delete(p)
            self.db.commit()
            console.print("[bold red]✘ Playlist removida.[/]")
            time.sleep(1)

    def manage_playlist_items(self):
        pid = self.prompt_int_or_cancel("ID da Playlist para gerenciar")
        if pid is None: return
        p = self.db.get(Playlist, pid)
        if not p: return

        while True:
            self.clear_screen()
            console.print(Panel(Text(f"Gerenciando Itens: {p.name}", style="bold magenta")))
            
            items = self.db.query(PlaylistItem).filter(PlaylistItem.playlist_id == pid).order_by(PlaylistItem.position).all()
            table = Table(box=box.SIMPLE)
            table.add_column("ORDEM")
            table.add_column("PAPEL")
            table.add_column("MÍDIA")
            
            for item in items:
                media = self.db.get(MediaItem, item.media_id)
                role_style = "cyan" if item.role == "OPENING" else "yellow" if item.role == "CLOSING" else "white"
                table.add_row(str(item.position), f"[{role_style}]{item.role}[/]", media.name if media else "N/A")
            
            console.print(table)
            console.print("\n[bold cyan][A] Adicionar[/] | [bold blue][M] Adição em Lote[/] | [bold yellow][E] Editar Item[/] | [bold red][D] Remover[/] | [bold white][V] Voltar[/]")
            
            opt = Prompt.ask("Opção", choices=["a", "m", "e", "d", "v"]).lower()
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
                    
                    if m_opt.lower() in ["v", "c"]: break
                    if m_opt.lower() == "n": m_page = (m_page + 1) % m_total_pages; continue
                    if m_opt.lower() == "p": m_page = (m_page - 1) % m_total_pages; continue
                    if m_opt.lower() == "g":
                        m_target = self.prompt_int_or_cancel(f"Ir para página (1-{m_total_pages})", allow_zero=True)
                        if m_target is not None and 1 <= m_target <= m_total_pages: m_page = m_target - 1
                        continue
                    
                    try:
                        mid = int(m_opt)
                        media = self.db.get(MediaItem, mid)
                        if media:
                            order = self.prompt_int_or_cancel("Ordem", allow_zero=True)
                            if order is None: order = len(items) + 1
                            
                            exists = self.db.query(PlaylistItem).filter_by(playlist_id=pid, position=order).first()
                            if exists:
                                console.print(f"[red]Já existe um item na ordem {order}![/]")
                                time.sleep(1.5)
                                continue
                                
                            role = Prompt.ask("Papel", choices=["OPENING", "CONTENT", "CLOSING"], default="CONTENT")
                            new_item = PlaylistItem(playlist_id=pid, media_id=mid, position=order, role=role)
                            self.db.add(new_item)
                            self.db.commit()
                            break
                    except:
                        console.print("[red]ID inválido.[/]")
                        time.sleep(1)
            
            elif opt == "m":
                mids_str = Prompt.ask("IDs das Mídias (ex: 1,3,5) ou V para cancelar", default="v")
                if mids_str.lower() not in ['v', 'c']:
                    role = Prompt.ask("Papel para todas", choices=["OPENING", "CONTENT", "CLOSING"], default="CONTENT")
                    start_order = self.prompt_int_or_cancel("Ordem Inicial (ou Enter para fim)", allow_zero=True)
                    if start_order is None: start_order = len(items) + 1
                    
                    added = 0
                    current_order = start_order
                    for m_s in mids_str.split(','):
                        try:
                            mid = int(m_s.strip())
                            if self.db.get(MediaItem, mid):
                                while self.db.query(PlaylistItem).filter_by(playlist_id=pid, position=current_order).first():
                                    current_order += 1
                                    
                                new_item = PlaylistItem(playlist_id=pid, media_id=mid, position=current_order, role=role)
                                self.db.add(new_item)
                                added += 1
                                current_order += 1
                        except ValueError: pass
                    self.db.commit()
                    console.print(f"[green]{added} item(ns) adicionado(s) em lote.[/]")
                    time.sleep(1.5)
            
            elif opt == "e":
                order = self.prompt_int_or_cancel("Ordem do item para editar", allow_zero=True)
                if order is not None:
                    item = self.db.query(PlaylistItem).filter_by(playlist_id=pid, position=order).first()
                    if item:
                        new_order = self.prompt_int_or_cancel("Nova Ordem (V=manter)", allow_zero=True)
                        if new_order is None: new_order = item.position
                        
                        if new_order != item.position:
                            exists = self.db.query(PlaylistItem).filter_by(playlist_id=pid, position=new_order).first()
                            if exists:
                                console.print(f"[red]Ordem {new_order} já está ocupada! Abortando.[/]")
                                time.sleep(1.5)
                                continue
                            item.position = new_order
                            
                        item.role = Prompt.ask("Novo Papel", choices=["OPENING", "CONTENT", "CLOSING"], default=item.role)
                        self.db.commit()
                        console.print("[green]Item atualizado.[/]")
                        time.sleep(1.5)
            
            elif opt == "d":
                order = self.prompt_int_or_cancel("Ordem do item para remover", allow_zero=True)
                if order is not None:
                    item = self.db.query(PlaylistItem).filter_by(playlist_id=pid, position=order).first()
                    if item: self.db.delete(item); self.db.commit()
