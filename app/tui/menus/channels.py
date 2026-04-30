import time
from datetime import datetime
from rich.table import Table
from rich import box
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from app.models import Channels, ChannelSchedule, Playlist, PlaylistItem, MediaItem
from app.tui.base import BaseMenu, console

class ChannelsMenu(BaseMenu):
    label = "Gerenciar Canais"
    order = 1

    def execute(self):
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
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold cyan][A][/] Adicionar | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold magenta][S][/] Agenda do Canal | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "a", "e", "d", "s", "v"]
            opt = Prompt.ask("Opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = self.prompt_int_or_cancel(f"Ir para página (1-{total_pages})", allow_zero=True)
                if target is not None and 1 <= target <= total_pages: page = target - 1
            
            if opt == "a": self.add_channel()
            elif opt == "e": self.edit_channel()
            elif opt == "d": self.delete_channel()
            elif opt == "s":
                cid = self.prompt_int_or_cancel("ID do Canal para gerenciar a agenda")
                if cid is not None:
                    ch = self.db.get(Channels, cid)
                    if ch:
                        self.manage_channel_schedules(cid, ch.name)
                    else:
                        console.print("[red]Canal não encontrado.[/]")
                        time.sleep(1)

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
        cids_str = Prompt.ask("IDs para deletar (ex: 1,3) ou V para voltar", default="v")
        if cids_str.lower() not in ['v', 'c']:
            removed = 0
            for c_str in cids_str.split(','):
                try:
                    cid = int(c_str.strip())
                    ch = self.db.get(Channels, cid)
                    if ch:
                        if Confirm.ask(f"Tem certeza que deseja deletar o canal '{ch.name}'?"):
                            self.db.delete(ch)
                            removed += 1
                except ValueError: pass
            if removed > 0:
                self.db.commit()
                console.print(f"[bold red]✘ {removed} Canal(is) removido(s).[/]")
            time.sleep(1.5)

    def edit_channel(self):
        cid = self.prompt_int_or_cancel("ID do Canal para editar")
        if cid is not None:
            ch = self.db.get(Channels, cid)
            if ch:
                while True:
                    self.clear_screen()
                    console.print(Panel(Text(f"Editando Canal: {ch.name}", style="bold cyan")))
                    console.print(f"[1] Nome (Atual: {ch.name})")
                    console.print(f"[2] Tipo (Atual: {ch.type})")
                    console.print(f"[3] Modo (Atual: {ch.execution_mode})")
                    console.print("[bold green][C][/] Salvar e Sair")
                    
                    opt = Prompt.ask("Opção", choices=["1", "2", "3", "c", "v"], default="c").lower()
                    if opt in ["c", "v"]:
                        break
                    if opt == "1":
                        ch.name = Prompt.ask("Novo Nome", default=ch.name)
                    elif opt == "2":
                        ch.type = Prompt.ask("Novo Tipo", choices=["TV", "RADIO"], default=ch.type)
                    elif opt == "3":
                        ch.execution_mode = Prompt.ask("Novo Modo", choices=["ALWAYS_ON", "ON_DEMAND", "PREDICTIVE"], default=ch.execution_mode)
                        
                self.db.commit()
                console.print("[bold green]✔ Canal atualizado![/]")
                time.sleep(1)

    # ----------------------------------------------------
    # MÉTODOS DE AGENDA (MIGRADOS)
    # ----------------------------------------------------

    def manage_channel_schedules(self, cid: int, cname: str):
        page = 0
        while True:
            self.clear_screen()
            console.print(Panel(Text(f"AGENDA DO CANAL: {cname} (ID: {cid})", style="bold magenta")))
            
            schedules_q = self.db.query(ChannelSchedule).filter_by(channel_id=cid)
            total = schedules_q.count()
            total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
            
            offset = page * self.page_size
            schedules = schedules_q.offset(offset).limit(self.page_size).all()
            
            table = Table(box=box.ROUNDED)
            table.add_column("ID")
            table.add_column("PLAYLIST")
            table.add_column("INÍCIO")
            table.add_column("FIM")
            table.add_column("DIAS", justify="center")

            for s in schedules:
                pl = self.db.get(Playlist, s.playlist_id)
                dias = "Todos"
                if s.weekdays: dias = f"Sem: {s.weekdays}"
                if s.month_days: dias = f"Mês: {s.month_days}"
                if s.weekdays and s.month_days: dias = f"S:{s.weekdays} M:{s.month_days}"
                
                table.add_row(
                    str(s.id),
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
            
            if opt == "a": self.add_schedule(cid)
            elif opt == "e": self.edit_schedule(cid)
            elif opt == "d": self.delete_schedule(cid)

    def _parse_days(self, prompt_text: str):
        val = Prompt.ask(prompt_text, default="")
        if val.lower() in ["vazio", ""]: return None
        try:
            return [int(x.strip()) for x in val.split(',') if x.strip().isdigit()]
        except:
            return None

    def _prompt_frequency(self, current_wd=None, current_md=None, is_edit=False):
        wd = current_wd
        md = current_md
        
        while True:
            self.clear_screen()
            console.print(Panel(Text("Configuração de Frequência", style="bold cyan")))
            
            if not wd and not md:
                console.print("[green]✔ Status Atual: Diário (Todos os dias)[/]\n")
            else:
                wd_str = f"Semana: {wd}" if wd else "Semana: Padrão"
                md_str = f"Mês: {md}" if md else "Mês: Padrão"
                console.print(f"[yellow]⚠ Status Atual: {wd_str} | {md_str}[/]\n")
                
            console.print("[1] Configurar Dias da Semana")
            console.print("[2] Configurar Dias do Mês")
            console.print("[3] Limpar Regras (Tornar Diário)")
            console.print("[bold green][C][/] Confirmar e Prosseguir")
            
            prompt_str = "Opção [Enter = confirmar]"
            opt = Prompt.ask(prompt_str, choices=["1", "2", "3", "c", ""], default="c").lower()
            
            if opt in ["c", ""]:
                return wd, md
                
            if opt == "3":
                wd = None
                md = None
            elif opt == "1":
                console.print("\n[dim]Legenda Semana: 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sáb, 6=Dom[/]")
                res = self._parse_days("Digite os números (ex: 0,2,4) ou vazio para remover a regra")
                wd = res
            elif opt == "2":
                res = self._parse_days("Digite os dias do mês (1 a 31, ex: 10,20) ou vazio para remover")
                md = res

    def _has_conflict(self, cid: int, st_time, et_time, exclude_sid=None) -> bool:
        schedules = self.db.query(ChannelSchedule).filter_by(channel_id=cid).all()
        for s in schedules:
            if exclude_sid and s.id == exclude_sid: continue
            if (st_time <= s.end_time) and (s.start_time <= et_time):
                return True
        return False

    def _select_playlist(self):
        pl_page = 0
        while True:
            self.clear_screen()
            pl_total = self.db.query(Playlist).count()
            pl_total_pages = (pl_total + self.page_size - 1) // self.page_size if pl_total > 0 else 1
            
            pl_offset = pl_page * self.page_size
            playlists = self.db.query(Playlist).offset(pl_offset).limit(self.page_size).all()
            
            pl_table = Table(title=f"Selecione a Playlist (Pág {pl_page+1} de {pl_total_pages})", box=box.ROUNDED)
            pl_table.add_column("ID", justify="center")
            pl_table.add_column("NOME", style="bold")
            pl_table.add_column("MODO", justify="center")
            
            for p in playlists: 
                pl_table.add_row(str(p.id), p.name, "SHUFFLE" if p.shuffle else "SEQUENCIAL")
            console.print(pl_table)
            
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold white][V][/] Voltar")
            pl_opt = Prompt.ask("Escolha o ID da Playlist ou Opção", default="v")
            
            if pl_opt.lower() in ["v", "c"]: return None
            if pl_opt.lower() == "n": pl_page = (pl_page + 1) % pl_total_pages; continue
            if pl_opt.lower() == "p": pl_page = (pl_page - 1) % pl_total_pages; continue
            if pl_opt.lower() == "g":
                p_target = self.prompt_int_or_cancel(f"Ir para página (1-{pl_total_pages})", allow_zero=True)
                if p_target is not None and 1 <= p_target <= pl_total_pages: pl_page = p_target - 1
                continue
            
            try:
                temp_pid = int(pl_opt.strip())
                if self.db.get(Playlist, temp_pid):
                    return temp_pid
                else:
                    console.print("[red]Playlist não encontrada.[/]")
                    time.sleep(1)
            except ValueError:
                console.print("[red]ID Inválido.[/]")
                time.sleep(1)

    def add_schedule(self, cid: int):
        pid = self._select_playlist()
        if pid is None: return
        
        start = Prompt.ask("Início (HH:MM) ou V para voltar")
        if start.lower() in ['v', 'c']: return
        
        end = Prompt.ask("Fim (HH:MM) [Enter p/ auto-calcular]", default="")
        
        weekdays, month_days = self._prompt_frequency(is_edit=False)
        
        try:
            from datetime import timedelta
            st_dt = datetime.strptime(start, "%H:%M")
            st = st_dt.time()
            
            if not end.strip():
                duration_sec = Playlist.calc_total_duration(self.db, pid)
                et_dt = st_dt + timedelta(seconds=duration_sec)
                et = et_dt.time()
                console.print(f"[cyan]Duração da playlist: {duration_sec}s | Fim calculado: {et.strftime('%H:%M')}[/]")
            else:
                et = datetime.strptime(end, "%H:%M").time()
            
            if self._has_conflict(cid, st, et):
                if not Confirm.ask("[yellow]Aviso: Existe conflito de horários neste canal! Deseja forçar?[/]"):
                    return
            
            sched = ChannelSchedule(channel_id=cid, playlist_id=pid, start_time=st, end_time=et, weekdays=weekdays, month_days=month_days)
            self.db.add(sched)
            self.db.commit()
            console.print("[bold green]✔ Agendamento criado para este canal![/]")
        except Exception as e:
            console.print(f"[bold red]Erro: {e}[/]")
        time.sleep(1.5)

    def edit_schedule(self, cid: int):
        sid = self.prompt_int_or_cancel("ID do agendamento para editar")
        if sid is None: return
        s = self.db.get(ChannelSchedule, sid)
        if s and s.channel_id == cid:
            while True:
                self.clear_screen()
                pl = self.db.get(Playlist, s.playlist_id)
                pl_name = pl.name if pl else "Desconhecida"
                
                wd_str = f"{s.weekdays}" if s.weekdays else "Padrão"
                md_str = f"{s.month_days}" if s.month_days else "Padrão"
                
                console.print(Panel(Text(f"Editando Agendamento {s.id}", style="bold yellow")))
                console.print(f"[1] Playlist   (Atual: ID {s.playlist_id} - {pl_name})")
                console.print(f"[2] Início     (Atual: {s.start_time.strftime('%H:%M')})")
                console.print(f"[3] Fim        (Atual: {s.end_time.strftime('%H:%M')})")
                console.print(f"[4] Frequência (Atual: Sem: {wd_str} | Mês: {md_str})")
                console.print("[bold green][C][/] Salvar e Sair")
                
                opt = Prompt.ask("Opção", choices=["1", "2", "3", "4", "c", "v"], default="c").lower()
                if opt in ["c", "v"]:
                    break
                    
                if opt == "1":
                    pid = self._select_playlist()
                    if pid is not None: s.playlist_id = pid
                elif opt == "2":
                    st_str = Prompt.ask("Novo Início (HH:MM)")
                    try:
                        s.start_time = datetime.strptime(st_str, "%H:%M").time()
                    except ValueError:
                        console.print("[red]Formato inválido.[/]"); time.sleep(1)
                elif opt == "3":
                    et_str = Prompt.ask("Novo Fim (HH:MM)")
                    try:
                        s.end_time = datetime.strptime(et_str, "%H:%M").time()
                    except ValueError:
                        console.print("[red]Formato inválido.[/]"); time.sleep(1)
                elif opt == "4":
                    wd, md = self._prompt_frequency(current_wd=s.weekdays, current_md=s.month_days, is_edit=True)
                    s.weekdays = wd
                    s.month_days = md
                    
            try:
                if self._has_conflict(cid, s.start_time, s.end_time, exclude_sid=s.id):
                    if not Confirm.ask("[yellow]Aviso: Existe conflito de horários neste canal! Deseja forçar o salvamento?[/]"):
                        return
                
                self.db.commit()
                console.print("[green]Agendamento atualizado![/]")
            except Exception as e:
                console.print(f"[bold red]Erro ao atualizar agendamento: {e}[/]")
            time.sleep(1.5)
        else:
            console.print("[red]ID de agendamento não encontrado neste canal.[/]")
            time.sleep(1.5)

    def delete_schedule(self, cid: int):
        sids_str = Prompt.ask("IDs para deletar (ex: 1,3) ou V para voltar", default="v")
        if sids_str.lower() not in ['v', 'c']:
            removed = 0
            for s_str in sids_str.split(','):
                try:
                    sid = int(s_str.strip())
                    s = self.db.get(ChannelSchedule, sid)
                    if s and s.channel_id == cid:
                        self.db.delete(s)
                        removed += 1
                except ValueError: pass
            if removed > 0:
                self.db.commit()
                console.print(f"[bold red]✘ {removed} Agendamento(s) removido(s).[/]")
            time.sleep(1.5)
