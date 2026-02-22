import time
from datetime import datetime
from rich.table import Table
from rich import box
from rich.prompt import Prompt, IntPrompt
from app.models import ChannelSchedule, Channels, Playlist
from app.tui.base import BaseMenu, console

class SchedulesMenu(BaseMenu):
    label = "📅 Gerenciar Agenda"
    order = 3

    def execute(self):
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
            
            if opt == "a": self.add_schedule()
            elif opt == "e": self.edit_schedule()
            elif opt == "d": self.delete_schedule()

    def add_schedule(self):
        cid = IntPrompt.ask("ID do Canal")
        pid = IntPrompt.ask("ID da Playlist")
        start = Prompt.ask("Início (HH:MM)")
        end = Prompt.ask("Fim (HH:MM)")
        
        try:
            st = datetime.strptime(start, "%H:%M").time()
            et = datetime.strptime(end, "%H:%M").time()
            
            sched = ChannelSchedule(channel_id=cid, playlist_id=pid, start_time=st, end_time=et)
            self.db.add(sched)
            self.db.commit()
            console.print("[bold green]✔ Agendamento criado![/]")
        except Exception as e:
            console.print(f"[bold red]Erro: {e}[/]")
        time.sleep(1)

    def edit_schedule(self):
        sid = IntPrompt.ask("ID do agendamento para editar")
        s = self.db.get(ChannelSchedule, sid)
        if s:
            s.channel_id = IntPrompt.ask("Novo ID do Canal", default=s.channel_id)
            s.playlist_id = IntPrompt.ask("Novo ID da Playlist", default=s.playlist_id)
            st_str = Prompt.ask("Novo Início (HH:MM)", default=s.start_time.strftime("%H:%M"))
            et_str = Prompt.ask("Novo Fim (HH:MM)", default=s.end_time.strftime("%H:%M"))
            try:
                s.start_time = datetime.strptime(st_str, "%H:%M").time()
                s.end_time = datetime.strptime(et_str, "%H:%M").time()
                self.db.commit(); console.print("[green]Agendamento atualizado![/]")
            except Exception as e:
                console.print(f"[bold red]Erro: {e}[/]")
            time.sleep(1)

    def delete_schedule(self):
        sid = IntPrompt.ask("ID do agendamento para deletar")
        s = self.db.get(ChannelSchedule, sid)
        if s: self.db.delete(s); self.db.commit(); console.print("[red]Removido.[/]"); time.sleep(1)
