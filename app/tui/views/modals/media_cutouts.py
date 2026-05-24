import os
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Label, Input, DataTable, Select
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

            # ── LINHA DE EXPORTAÇÃO ──
            with Horizontal(id="modal-export-row", classes="export-row"):
                yield Label("📤 Exportar como:", classes="export-label")
                yield Select(
                    [
                        ("EDL (MPlayer/Kodi)", "edl"),
                        ("XML (Padrão)", "xml"),
                        ("NFO (Kodi)", "nfo"),
                        ("STR (SubRip)", "str"),
                    ],
                    id="export-format-select",
                    value="edl",
                    prompt="Selecione o formato",
                )
                yield Button("Exportar", id="btn-export-cutouts", variant="primary")

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
        elif event.button.id == "btn-export-cutouts":
            self.action_export_cutouts()
            
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

    # ──────────────────────────────────────────────
    #  HELPERS DE TEMPO
    # ──────────────────────────────────────────────

    def _parse_hms(self, time_str: str) -> float:
        """Converte string HH:MM:SS.fff para segundos float."""
        if not time_str or not time_str.strip():
            return 0.0
        time_str = time_str.strip().replace(',', '.')
        parts = time_str.split(':')
        if len(parts) == 3:
            try:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            except ValueError:
                return 0.0
        elif len(parts) == 2:
            try:
                return int(parts[0]) * 60 + float(parts[1])
            except ValueError:
                return 0.0
        try:
            return float(time_str)
        except ValueError:
            return 0.0

    def _format_srt_time(self, sec: float) -> str:
        """Converte segundos float para formato SRT: HH:MM:SS,mmm"""
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')

    def _get_current_skips(self) -> dict:
        """Lê os valores atuais dos inputs e tabela de cortes."""
        skips = {}

        intro_start = self.query_one("#in-intro-start", Input).value.strip()
        intro_end = self.query_one("#in-intro-end", Input).value.strip()
        if intro_start or intro_end:
            skips["intro"] = {"start": intro_start, "end": intro_end}

        finish_start = self.query_one("#in-finish-start", Input).value.strip()
        finish_end = self.query_one("#in-finish-end", Input).value.strip()
        if finish_start or finish_end:
            skips["finish"] = {"start": finish_start, "end": finish_end}

        cuts = []
        table = self.query_one("#cuts-table", DataTable)
        for row_key in table.rows:
            row_data = table.get_row(row_key)
            cuts.append({"start": row_data[0], "end": row_data[1]})
        if cuts:
            skips["cuts"] = cuts

        return skips

    # ──────────────────────────────────────────────
    #  EXPORTAR CUTOUTS (AÇÃO PRINCIPAL)
    # ──────────────────────────────────────────────

    def action_export_cutouts(self) -> None:
        """Exporta os cutouts atuais no formato selecionado via diálogo nativo."""
        import tkinter as tk
        from tkinter import filedialog

        fmt = self.query_one("#export-format-select", Select).value
        if not fmt:
            self.app.notify("Selecione um formato de exportação.", severity="warning")
            return

        skips = self._get_current_skips()
        if not skips.get("intro") and not skips.get("finish") and not skips.get("cuts"):
            self.app.notify("Nenhum cutout para exportar. Preencha os campos primeiro.", severity="warning")
            return

        ext_map = {"edl": ".edl", "xml": ".xml", "nfo": ".nfo", "str": ".str"}
        desc_map = {
            "edl": "EDL (MPlayer/Kodi)",
            "xml": "XML (Padrão)",
            "nfo": "NFO (Kodi)",
            "str": "STR (SubRip)",
        }

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        file_path = filedialog.asksaveasfilename(
            parent=root,
            title=f"Exportar Cutouts — {desc_map.get(fmt, fmt.upper())}",
            defaultextension=ext_map.get(fmt, ".txt"),
            filetypes=[
                (desc_map.get(fmt, fmt.upper()), f"*{ext_map.get(fmt, '.txt')}"),
                ("Todos os arquivos", "*.*"),
            ],
            initialfile=f"cutouts_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext_map.get(fmt, '.txt')}",
        )
        root.destroy()

        if not file_path:
            return  # Usuário cancelou

        try:
            if fmt == "edl":
                content = self._generate_edl(skips)
            elif fmt == "xml":
                content = self._generate_xml(skips)
            elif fmt == "nfo":
                content = self._generate_nfo(skips)
            elif fmt == "str":
                content = self._generate_str(skips)
            else:
                self.app.notify(f"Formato não suportado: {fmt}", severity="error")
                return

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.app.notify(
                f"✅ Cutouts exportados como {fmt.upper()}: {os.path.basename(file_path)}",
                severity="success",
            )
        except Exception as e:
            self.app.notify(f"Erro ao exportar: {e}", severity="error")

    # ──────────────────────────────────────────────
    #  GERADORES DE FORMATO
    # ──────────────────────────────────────────────

    def _generate_edl(self, skips: dict) -> str:
        """Gera conteúdo no formato EDL (MPlayer/Kodi)."""
        lines = []
        intro = skips.get("intro", {})
        if intro.get("start") and intro.get("end"):
            s = self._parse_hms(intro["start"])
            e = self._parse_hms(intro["end"])
            if e > s:
                lines.append(f"{s:.3f}\t{e:.3f}\t0")

        finish = skips.get("finish", {})
        if finish.get("start") and finish.get("end"):
            s = self._parse_hms(finish["start"])
            e = self._parse_hms(finish["end"])
            if e > s:
                lines.append(f"{s:.3f}\t{e:.3f}\t0")

        for cut in skips.get("cuts", []):
            s = self._parse_hms(cut.get("start", ""))
            e = self._parse_hms(cut.get("end", ""))
            if e > s:
                lines.append(f"{s:.3f}\t{e:.3f}\t0")

        return "\n".join(lines) + "\n"

    def _generate_xml(self, skips: dict) -> str:
        """Gera conteúdo no formato XML padrão."""
        root = ET.Element("cutouts")

        intro = skips.get("intro", {})
        if intro.get("start") or intro.get("end"):
            el = ET.SubElement(root, "intro")
            el.set("start", intro.get("start", ""))
            el.set("end", intro.get("end", ""))

        finish = skips.get("finish", {})
        if finish.get("start") or finish.get("end"):
            el = ET.SubElement(root, "finish")
            el.set("start", finish.get("start", ""))
            el.set("end", finish.get("end", ""))

        for cut in skips.get("cuts", []):
            el = ET.SubElement(root, "cut")
            el.set("start", cut.get("start", ""))
            el.set("end", cut.get("end", ""))

        ET.indent(root, space="  ")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")

    def _generate_nfo(self, skips: dict) -> str:
        """Gera conteúdo no formato NFO (Kodi)."""
        root = ET.Element("episodedetails")
        edl = ET.SubElement(root, "edl")

        intro = skips.get("intro", {})
        if intro.get("start") or intro.get("end"):
            bm = ET.SubElement(edl, "epbookmark")
            bm.set("type", "intro")
            bm.set("start", str(self._parse_hms(intro.get("start", ""))))
            bm.set("end", str(self._parse_hms(intro.get("end", ""))))

        finish = skips.get("finish", {})
        if finish.get("start") or finish.get("end"):
            bm = ET.SubElement(edl, "epbookmark")
            bm.set("type", "credits")
            bm.set("start", str(self._parse_hms(finish.get("start", ""))))
            bm.set("end", str(self._parse_hms(finish.get("end", ""))))

        for cut in skips.get("cuts", []):
            cut_el = ET.SubElement(root, "cut")
            start_el = ET.SubElement(cut_el, "start")
            start_el.text = str(self._parse_hms(cut.get("start", "")))
            end_el = ET.SubElement(cut_el, "end")
            end_el.text = str(self._parse_hms(cut.get("end", "")))

        ET.indent(root, space="  ")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")

    def _generate_str(self, skips: dict) -> str:
        """Gera conteúdo no formato STR (SubRip)."""
        lines = []
        idx = 1

        intro = skips.get("intro", {})
        if intro.get("start") or intro.get("end"):
            s = self._parse_hms(intro.get("start", ""))
            e = self._parse_hms(intro.get("end", ""))
            if e > s:
                lines.append(str(idx))
                lines.append(f"{self._format_srt_time(s)} --> {self._format_srt_time(e)}")
                lines.append("Intro - Abertura")
                lines.append("")
                idx += 1

        for i, cut in enumerate(skips.get("cuts", []), 1):
            s = self._parse_hms(cut.get("start", ""))
            e = self._parse_hms(cut.get("end", ""))
            if e > s:
                lines.append(str(idx))
                lines.append(f"{self._format_srt_time(s)} --> {self._format_srt_time(e)}")
                lines.append(f"Corte Comercial {i}")
                lines.append("")
                idx += 1

        finish = skips.get("finish", {})
        if finish.get("start") or finish.get("end"):
            s = self._parse_hms(finish.get("start", ""))
            e = self._parse_hms(finish.get("end", ""))
            if e > s:
                lines.append(str(idx))
                lines.append(f"{self._format_srt_time(s)} --> {self._format_srt_time(e)}")
                lines.append("Créditos - Encerramento")
                lines.append("")
                idx += 1

        return "\n".join(lines)
