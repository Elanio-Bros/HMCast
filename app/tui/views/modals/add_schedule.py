from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Select, Button, Label, Static
from textual.containers import Vertical, Horizontal
from datetime import time
import re


class AddScheduleModal(ModalScreen[bool]):
    """Modal de Agendamento com Validação de Conflitos."""
    
    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("VINCULAR PLAYLIST (AGENDAMENTO)", id="modal-title")
            
            with Vertical(classes="input-group"):
                yield Label("Playlist:")
                yield Select([], id="select-playlist", prompt="Selecione...")
            
            with Horizontal(classes="input-group-row"):
                with Vertical(classes="col"):
                    yield Label("Início:")
                    yield Input(placeholder="00:00", id="start-time")
                with Vertical(classes="col"):
                    yield Label("Fim:")
                    yield Input(placeholder="00:00", id="end-time")
            
            with Vertical(classes="input-group"):
                yield Label("Data/Dias (ex: mon, 15, 15/04, 20/05/2025):")
                yield Input(placeholder="Vazio para todos os dias", id="date-patterns")
            
            # Label para mensagens de erro
            yield Label("", id="error-message", classes="error-text")
            
            with Horizontal(id="modal-actions"):
                yield Button("Vincular", variant="success", id="btn-save")
                yield Button("Cancelar", variant="error", id="btn-cancel")

    def on_mount(self) -> None:
        from app.database import SessionLocal
        from app.models import Playlist
        
        select = self.query_one("#select-playlist", Select)
        with SessionLocal() as db:
            playlists = db.query(Playlist).all()
            options = [(p.name, p.id) for p in playlists]
            select.set_options(options)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.save_schedule()

    def save_schedule(self) -> None:
        from app.database import SessionLocal
        from app.models import ChannelSchedule
        
        playlist_id = self.query_one("#select-playlist", Select).value
        start_str = self.query_one("#start-time", Input).value
        end_str = self.query_one("#end-time", Input).value
        patterns_str = self.query_one("#date-patterns", Input).value.strip()
        error_lab = self.query_one("#error-message", Label)
        
        if not playlist_id or not start_str or not end_str:
            error_lab.update("Preencha todos os campos obrigatórios!")
            return

        try:
            sh, sm = map(int, start_str.split(':'))
            eh, em = map(int, end_str.split(':'))
            start_t = time(sh, sm)
            end_t = time(eh, em)
        except Exception:
            error_lab.update("Formato de hora inválido (Use HH:MM)")
            return
            
        # Lógica de Parsing Inteligente
        weekdays = []
        month_days = []
        specific_dates = []
        
        if patterns_str:
            parts = [p.strip().lower() for p in patterns_str.split(',')]
            for p in parts:
                if p in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                    weekdays.append(p)
                elif p.isdigit():
                    month_days.append(int(p))
                elif re.match(r"^\d{1,2}/\d{1,2}(/\d{4})?$", p):
                    specific_dates.append(p)
        
        with SessionLocal() as db:
            # VERIFICAÇÃO DE CONFLITO NO CORE
            conflict = ChannelSchedule.check_conflict(
                db, self.channel_id, start_t, end_t, 
                weekdays, month_days, specific_dates
            )
            
            if conflict:
                error_lab.update(conflict)
                return
            
            # SALVAMENTO
            new_sch = ChannelSchedule(
                channel_id=self.channel_id,
                playlist_id=playlist_id,
                start_time=start_t,
                end_time=end_t,
                weekdays=weekdays if weekdays else None,
                month_days=month_days if month_days else None,
                specific_dates=specific_dates if specific_dates else None
            )
            db.add(new_sch)
            db.commit()
            
        self.dismiss(True)
