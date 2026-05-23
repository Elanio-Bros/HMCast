from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Label, Input, DataTable
from textual.containers import Vertical, Horizontal, Grid
from app.database import SessionLocal
from app.models import MediaItem

class MediaCutoutsModal(ModalScreen[bool]):
    """Modal para gerenciar os recortes (skips/cuts) de um vídeo."""

    def __init__(self, media_id: int):
        super().__init__()
        self.media_id = media_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("GERENCIAR CORTES (CUTOUTS)", id="modal-title")
            
            with Horizontal(classes="input-group-row"):
                with Vertical(classes="col"):
                    yield Label("Abertura (Intro) - Início:")
                    yield Input(placeholder="00:00:00", id="in-intro-start")
                with Vertical(classes="col"):
                    yield Label("Abertura (Intro) - Fim:")
                    yield Input(placeholder="00:00:00", id="in-intro-end")
                    
            with Horizontal(classes="input-group-row"):
                with Vertical(classes="col"):
                    yield Label("Créditos (Finish) - Início:")
                    yield Input(placeholder="00:00:00", id="in-finish-start")
                with Vertical(classes="col"):
                    yield Label("Créditos (Finish) - Fim:")
                    yield Input(placeholder="00:00:00", id="in-finish-end")

            yield Label("Outros (Cortes Comerciais, etc):", classes="section-label")
            with Horizontal(classes="cuts-input-row"):
                yield Input(placeholder="Início (00:00:00)", id="in-cut-start")
                yield Input(placeholder="Fim (00:00:00)", id="in-cut-end")
                yield Button("Adicionar", id="btn-add-cut", variant="primary")
                yield Button("Remover", id="btn-remove-cut", variant="error")
                
            yield DataTable(id="cuts-table")
            
            yield Label("", id="cutout-error-message", classes="error-text")

            with Horizontal(id="modal-actions"):
                yield Button("Rodar Análise (FFmpeg)", variant="warning", id="btn-run-ffmpeg")
                yield Button("Salvar Manual", variant="success", id="btn-save-cutouts")
                yield Button("Fechar", id="btn-close-cutouts")

    def on_mount(self) -> None:
        table = self.query_one("#cuts-table", DataTable)
        table.add_columns("Início", "Fim")
        table.zebra_stripes = True
        table.cursor_type = "row"
        self.load_data()

    def load_data(self):
        with SessionLocal() as db:
            media = db.query(MediaItem).get(self.media_id)
            if not media:
                return
            
            skips = media.skips or {}
            
            intro = skips.get("intro", {})
            self.query_one("#in-intro-start", Input).value = intro.get("start", "")
            self.query_one("#in-intro-end", Input).value = intro.get("end", "")
            
            finish = skips.get("finish", {})
            self.query_one("#in-finish-start", Input).value = finish.get("start", "")
            self.query_one("#in-finish-end", Input).value = finish.get("end", "")
            
            table = self.query_one("#cuts-table", DataTable)
            table.clear()
            for cut in skips.get("cuts", []):
                table.add_row(cut.get("start", ""), cut.get("end", ""))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-cutouts":
            self.dismiss(True)
        elif event.button.id == "btn-save-cutouts":
            self.save_manual_cutouts()
        elif event.button.id == "btn-run-ffmpeg":
            self.run_ffmpeg_analysis()
        elif event.button.id == "btn-add-cut":
            self.action_add_cut()
        elif event.button.id == "btn-remove-cut":
            self.action_remove_cut()
            
    def action_add_cut(self):
        start = self.query_one("#in-cut-start", Input).value.strip()
        end = self.query_one("#in-cut-end", Input).value.strip()
        if start and end:
            table = self.query_one("#cuts-table", DataTable)
            table.add_row(start, end)
            self.query_one("#in-cut-start", Input).value = ""
            self.query_one("#in-cut-end", Input).value = ""
            
    def action_remove_cut(self):
        table = self.query_one("#cuts-table", DataTable)
        if table.cursor_coordinate and table.is_valid_coordinate(table.cursor_coordinate):
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key:
                table.remove_row(row_key)

    def save_manual_cutouts(self):
        # Lógica simplificada de salvamento
        intro_start = self.query_one("#in-intro-start", Input).value.strip()
        intro_end = self.query_one("#in-intro-end", Input).value.strip()
        finish_start = self.query_one("#in-finish-start", Input).value.strip()
        finish_end = self.query_one("#in-finish-end", Input).value.strip()

        skips = {}
        if intro_start or intro_end:
            skips["intro"] = {"start": intro_start or "00:00:00", "end": intro_end}
        if finish_start or finish_end:
            skips["finish"] = {"start": finish_start, "end": finish_end or "00:00:00"}
            
        # Ler os cortes adicionais diretamente da tabela
        cuts = []
        table = self.query_one("#cuts-table", DataTable)
        for row_key in table.rows:
            row_data = table.get_row(row_key)
            cuts.append({"start": row_data[0], "end": row_data[1]})
            
        if cuts:
            skips["cuts"] = cuts

        with SessionLocal() as db:
            media = db.query(MediaItem).get(self.media_id)
            if media:
                media.skips = skips
                db.commit()
                
        self.app.notify("Recortes salvos com sucesso!")
        self.dismiss(True)

    def run_ffmpeg_analysis(self):
        self.app.notify("Iniciando Análise Profunda em Background...")
        
        async def background_analysis():
            with SessionLocal() as db:
                media = db.query(MediaItem).get(self.media_id)
                if not media: return
                file_path = media.file
                
            from app.services.cutouts import CutoutAnalyzer
            from app.media_utils import MediaUtils
            utils = MediaUtils()
            analyzer = CutoutAnalyzer(ffmpeg_bin=utils.ffmpeg)
            
            try:
                # O processamento pesado
                cuts = analyzer.analyze(file_path)
                
                # Formata os tempos
                def format_time(sec: float):
                    h = int(sec // 3600)
                    m = int((sec % 3600) // 60)
                    s = sec % 60
                    return f"{h:02d}:{m:02d}:{s:06.3f}"
                    
                formatted_cuts = [{"start": format_time(c["start"]), "end": format_time(c["end"])} for c in cuts]
                
                if formatted_cuts:
                    with SessionLocal() as db:
                        media = db.query(MediaItem).get(self.media_id)
                        if media:
                            skips = media.skips or {}
                            skips["cuts"] = formatted_cuts
                            media.skips = skips
                            db.commit()
                            
                    def on_complete():
                        self.load_data()
                        self.app.notify(f"Análise concluída! Encontrados {len(formatted_cuts)} possíveis cortes.", severity="success")
                    self.app.call_from_thread(on_complete)
                else:
                    self.app.call_from_thread(lambda: self.app.notify("Análise concluída. Nenhum corte longo encontrado.", severity="warning"))
                    
            except Exception as e:
                self.app.call_from_thread(lambda: self.app.notify(f"Erro na análise: {e}", severity="error"))
                
        self.run_worker(background_analysis(), thread=True)
