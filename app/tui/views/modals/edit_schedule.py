from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Select, Button, Label, Static, Checkbox, DataTable
from textual.containers import Vertical, Horizontal
from app.database import SessionLocal
from app.models import ChannelSchedule, Playlist
from datetime import time, datetime, timedelta
import re


class EditScheduleModal(ModalScreen[bool]):
    """Modal de Edição de Agendamento."""
    
    def __init__(self, schedule_id: int):
        super().__init__()
        self.schedule_id = schedule_id
        self.channel_id = None

    def compose(self) -> ComposeResult:
        with Vertical(id="schedule-modal-container"):
            yield Static("EDITAR AGENDAMENTO", id="modal-title")
            
            with Vertical(classes="input-group"):
                yield Label("Playlist:")
                yield Select([], id="select-playlist", prompt="Selecione...")
            
            with Horizontal(classes="input-group-row"):
                with Vertical(classes="col"):
                    yield Label("Início:")
                    yield Input(placeholder="00:00", id="start-time")
                with Vertical(classes="col"):
                    yield Label("Fim (Vazio = Auto):")
                    yield Input(placeholder="Opcional", id="end-time")
            
            with Vertical(classes="auto-group"):
                yield Label("Dias da Semana:")
                with Horizontal(classes="checkbox-row"):
                    yield Button("Todas", id="btn-check-all", classes="btn-action-small")
                    yield Checkbox("Seg", id="chk-mon")
                    yield Checkbox("Ter", id="chk-tue")
                    yield Checkbox("Qua", id="chk-wed")
                    yield Checkbox("Qui", id="chk-thu")
                    yield Checkbox("Sex", id="chk-fri")
                    yield Checkbox("Sáb", id="chk-sat")
                    yield Checkbox("Dom", id="chk-sun")

            with Vertical(classes="auto-group"):
                yield Label("Datas Específicas ou Dias do Mês:")
                with Horizontal(classes="dates-input-row"):
                    yield Input(placeholder="Ex: 15 ou 15/04/2026", id="in-date")
                    yield Button("Adicionar", id="btn-add-date", variant="primary")
                    yield Button("Remover", id="btn-remove-date", variant="error")
                yield DataTable(id="dates-table")
            
            yield Label("", id="error-message", classes="error-text")
            
            with Horizontal(id="modal-actions"):
                yield Button("Salvar", variant="success", id="btn-save")
                yield Button("Cancelar", variant="error", id="btn-cancel")

    def on_mount(self) -> None:
        table = self.query_one("#dates-table", DataTable)
        table.add_column("Data / Dia do Mês")
        table.zebra_stripes = True
        table.cursor_type = "row"

        select = self.query_one("#select-playlist", Select)
        with SessionLocal() as db:
            playlists = db.query(Playlist).all()
            options = [(p.name, p.id) for p in playlists]
            select.set_options(options)
            
            sch = db.query(ChannelSchedule).get(self.schedule_id)
            if sch:
                self.channel_id = sch.channel_id
                select.value = sch.playlist_id
                self.query_one("#start-time", Input).value = sch.start_time.strftime("%H:%M")
                self.query_one("#end-time", Input).value = sch.end_time.strftime("%H:%M")
                
                # Checkboxes dos dias da semana
                if sch.weekdays:
                    days_map = {
                        "mon": "#chk-mon", "tue": "#chk-tue", "wed": "#chk-wed",
                        "thu": "#chk-thu", "fri": "#chk-fri", "sat": "#chk-sat", "sun": "#chk-sun"
                    }
                    for day_code in sch.weekdays:
                        if day_code in days_map:
                            self.query_one(days_map[day_code], Checkbox).value = True
                
                # Popula tabela
                if sch.month_days:
                    for md in sch.month_days:
                        table.add_row(str(md))
                if sch.specific_dates:
                    for sd in sch.specific_dates:
                        table.add_row(sd)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.save_schedule()
        elif event.button.id == "btn-add-date":
            self.action_add_date()
        elif event.button.id == "btn-remove-date":
            self.action_remove_date()
        elif event.button.id == "btn-check-all":
            self.action_check_all()

    def action_check_all(self) -> None:
        ids = ["#chk-mon", "#chk-tue", "#chk-wed", "#chk-thu", "#chk-fri", "#chk-sat", "#chk-sun"]
        first_state = self.query_one(ids[0], Checkbox).value
        new_state = not first_state
        for cid in ids:
            self.query_one(cid, Checkbox).value = new_state

    def action_add_date(self) -> None:
        in_date = self.query_one("#in-date", Input)
        val = in_date.value.strip()
        if val:
            table = self.query_one("#dates-table", DataTable)
            table.add_row(val)
            in_date.value = ""

    def action_remove_date(self) -> None:
        table = self.query_one("#dates-table", DataTable)
        if table.cursor_coordinate and table.is_valid_coordinate(table.cursor_coordinate):
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key:
                table.remove_row(row_key)

    def save_schedule(self) -> None:
        playlist_id = self.query_one("#select-playlist", Select).value
        start_str = self.query_one("#start-time", Input).value.strip()
        end_str = self.query_one("#end-time", Input).value.strip()
        error_lab = self.query_one("#error-message", Label)
        
        if not playlist_id or not start_str:
            error_lab.update("Playlist e Início são obrigatórios!")
            return

        try:
            sh, sm = map(int, start_str.split(':'))
            start_t = time(sh, sm)
        except Exception:
            error_lab.update("Formato de Início inválido (Use HH:MM)")
            return

        with SessionLocal() as db:
            if not end_str:
                duration_sec = Playlist.calc_total_duration(db, playlist_id)
                if duration_sec <= 0:
                    error_lab.update("Playlist vazia ou sem duração válida!")
                    return
                dummy_date = datetime.combine(datetime.today(), start_t)
                end_dt = dummy_date + timedelta(seconds=duration_sec)
                end_t = end_dt.time()
            else:
                try:
                    eh, em = map(int, end_str.split(':'))
                    end_t = time(eh, em)
                except Exception:
                    error_lab.update("Formato de Fim inválido (Use HH:MM)")
                    return
            
            # Coleta Dias da Semana
            weekdays = []
            days_map = {
                "#chk-mon": "mon", "#chk-tue": "tue", "#chk-wed": "wed",
                "#chk-thu": "thu", "#chk-fri": "fri", "#chk-sat": "sat", "#chk-sun": "sun"
            }
            for cid, day_code in days_map.items():
                if self.query_one(cid, Checkbox).value:
                    weekdays.append(day_code)

            # Coleta Datas da Tabela
            month_days = []
            specific_dates = []
            table = self.query_one("#dates-table", DataTable)
            for row_key in table.rows:
                val = str(table.get_row(row_key)[0]).strip().lower()
                if val.isdigit():
                    month_days.append(int(val))
                elif re.match(r"^\d{1,2}/\d{1,2}(/\d{4})?$", val):
                    specific_dates.append(val)
            
            conflict = ChannelSchedule.check_conflict(
                db, self.channel_id, start_t, end_t, 
                weekdays, month_days, specific_dates, exclude_id=self.schedule_id
            )
            
            if conflict:
                error_lab.update(conflict)
                return
            
            sch = db.query(ChannelSchedule).get(self.schedule_id)
            if sch:
                sch.playlist_id = playlist_id
                sch.start_time = start_t
                sch.end_time = end_t
                sch.weekdays = weekdays if weekdays else None
                sch.month_days = month_days if month_days else None
                sch.specific_dates = specific_dates if specific_dates else None
                db.commit()
            
        self.dismiss(True)
