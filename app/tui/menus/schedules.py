import time
from datetime import datetime
from rich.table import Table
from rich import box
from rich.prompt import Prompt, IntPrompt
from app.models import ChannelSchedule, Channels, Playlist
from app.tui.base import BaseMenu, console

class SchedulesMenu(BaseMenu):
    label = "Gerenciar Agenda"
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
            table.add_column("DIAS", justify="center")

            for s in schedules:
                ch = self.db.get(Channels, s.channel_id)
                pl = self.db.get(Playlist, s.playlist_id)
                dias = "Todos"
                if s.weekdays: dias = f"Sem: {s.weekdays}"
                if s.month_days: dias = f"Mês: {s.month_days}"
                if s.weekdays and s.month_days: dias = f"S:{s.weekdays} M:{s.month_days}"
                
                table.add_row(
                    str(s.id),
                    ch.name if ch else "N/A",
                    pl.name if pl else "N/A",
                    s.start_time.strftime("%H:%M"),
                    s.end_time.strftime("%H:%M"),
                    dias
                )
            
            console.print(table)
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold cyan][A][/] Adicionar | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "a", "e", "d", "v"]
            opt = Prompt.ask("Opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = self.prompt_int_or_cancel(f"Ir para página (1-{total_pages})", allow_zero=True)
                if target is not None and 1 <= target <= total_pages: page = target - 1
            
            if opt == "a": self.add_schedule()
            elif opt == "e": self.edit_schedule()
            elif opt == "d": self.delete_schedule()

    def _calc_playlist_duration(self, pid: int) -> int:
        from app.models import PlaylistItem, MediaItem
        items = self.db.query(PlaylistItem).filter_by(playlist_id=pid).order_by(PlaylistItem.position).all()
        total = 0
        for i, item in enumerate(items):
            media = self.db.get(MediaItem, item.media_id)
            if not media: continue
            
            skips = media.skips or {}
            duration = float(media.duration)
            is_first = (i == 0)
            is_last = (i == len(items) - 1)
            
            if "intro" in skips and not is_first:
                st = media.hms_to_seconds(skips["intro"]["start"])
                et = media.hms_to_seconds(skips["intro"]["end"])
                duration -= max(0, et - st)
            
            if "finish" in skips and not is_last:
                st = media.hms_to_seconds(skips["finish"]["start"])
                et = float(media.duration)
                duration -= max(0, et - st)
                
            if "cuts" in skips:
                for cut in skips.get("cuts", []):
                    st = media.hms_to_seconds(cut["start"])
                    et = media.hms_to_seconds(cut["end"])
                    duration -= max(0, et - st)
                    
            total += max(0, duration)
        return int(total)

    def _parse_days(self, prompt_text: str):
        val = Prompt.ask(prompt_text, default="vazio")
        if val.lower() in ["vazio", ""]: return None
        try:
            return [int(x.strip()) for x in val.split(',') if x.strip().isdigit()]
        except:
            return None

    def _has_conflict(self, cid: int, st_time, et_time, exclude_sid=None) -> bool:
        schedules = self.db.query(ChannelSchedule).filter_by(channel_id=cid).all()
        for s in schedules:
            if exclude_sid and s.id == exclude_sid: continue
            if (st_time <= s.end_time) and (s.start_time <= et_time):
                return True
        return False

    def add_schedule(self):
        cid = self.prompt_int_or_cancel("ID do Canal")
        if cid is None: return
        pid = self.prompt_int_or_cancel("ID da Playlist")
        if pid is None: return
        
        start = Prompt.ask("Início (HH:MM) ou V para voltar")
        if start.lower() in ['v', 'c']: return
        
        end = Prompt.ask("Fim (HH:MM) [Deixe vazio para auto-calcular]", default="")
        
        weekdays = self._parse_days("Dias da Semana (0-6, ex: 0,1,2 ou vazio para todos)")
        month_days = self._parse_days("Dias do Mês (1-31, ex: 10,20 ou vazio para todos)")
        
        try:
            from datetime import timedelta
            st_dt = datetime.strptime(start, "%H:%M")
            st = st_dt.time()
            
            if not end.strip():
                duration_sec = self._calc_playlist_duration(pid)
                et_dt = st_dt + timedelta(seconds=duration_sec)
                et = et_dt.time()
                console.print(f"[cyan]Duração da playlist: {duration_sec}s | Fim calculado: {et.strftime('%H:%M')}[/]")
            else:
                et = datetime.strptime(end, "%H:%M").time()
            
            if self._has_conflict(cid, st, et):
                from rich.prompt import Confirm
                if not Confirm.ask("[yellow]Aviso: Existe conflito de horários neste canal! Deseja forçar?[/]"):
                    return
            
            sched = ChannelSchedule(channel_id=cid, playlist_id=pid, start_time=st, end_time=et, weekdays=weekdays, month_days=month_days)
            self.db.add(sched)
            self.db.commit()
            console.print("[bold green]✔ Agendamento criado![/]")
        except Exception as e:
            console.print(f"[bold red]Erro: {e}[/]")
        time.sleep(1.5)

    def edit_schedule(self):
        sid = self.prompt_int_or_cancel("ID do agendamento para editar")
        if sid is None: return
        s = self.db.get(ChannelSchedule, sid)
        if s:
            cid = self.prompt_int_or_cancel(f"Novo ID do Canal (Atual: {s.channel_id})", allow_zero=True)
            if cid is not None: s.channel_id = cid
            
            pid = self.prompt_int_or_cancel(f"Novo ID da Playlist (Atual: {s.playlist_id})", allow_zero=True)
            if pid is not None: s.playlist_id = pid
            
            st_str = Prompt.ask("Novo Início (HH:MM)", default=s.start_time.strftime("%H:%M"))
            et_str = Prompt.ask("Novo Fim (HH:MM)", default=s.end_time.strftime("%H:%M"))
            
            wd = Prompt.ask(f"Dias da Semana", default=str(s.weekdays or "vazio"))
            md = Prompt.ask(f"Dias do Mês", default=str(s.month_days or "vazio"))
            
            try:
                if wd and wd != "vazio": 
                    s.weekdays = [int(x.strip()) for x in wd.replace('[','').replace(']','').split(',') if x.strip().isdigit()]
                else: s.weekdays = None
                
                if md and md != "vazio": 
                    s.month_days = [int(x.strip()) for x in md.replace('[','').replace(']','').split(',') if x.strip().isdigit()]
                else: s.month_days = None

                st = datetime.strptime(st_str, "%H:%M").time()
                et = datetime.strptime(et_str, "%H:%M").time()
                
                if self._has_conflict(s.channel_id, st, et, exclude_sid=s.id):
                    from rich.prompt import Confirm
                    if not Confirm.ask("[yellow]Aviso: Existe conflito de horários neste canal! Deseja forçar?[/]"):
                        return
                        
                s.start_time = st
                s.end_time = et
                self.db.commit(); console.print("[green]Agendamento atualizado![/]")
            except Exception as e:
                console.print(f"[bold red]Erro: {e}[/]")
            time.sleep(1.5)

    def delete_schedule(self):
        sid = self.prompt_int_or_cancel("ID do agendamento para deletar")
        if sid is None: return
        s = self.db.get(ChannelSchedule, sid)
        if s: self.db.delete(s); self.db.commit(); console.print("[red]Removido.[/]"); time.sleep(1)
