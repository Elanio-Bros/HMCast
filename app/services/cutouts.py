import os
import json
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
import re
import subprocess
import os
import re
from typing import List, Dict

@dataclass
class TimeRange:
    start: float
    end: float

    def to_dict(self):
        def format_time(sec: float):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = sec % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}"
        
        return {
            "start": format_time(self.start),
            "end": format_time(self.end)
        }

@dataclass
class CutoutMetadata:
    intro: Optional[TimeRange] = None
    finish: Optional[TimeRange] = None
    cuts: List[TimeRange] = field(default_factory=list)

    def to_dict(self):
        res = {}
        if self.intro:
            res["intro"] = self.intro.to_dict()
        if self.finish:
            res["finish"] = self.finish.to_dict()
        if self.cuts:
            res["cuts"] = [c.to_dict() for c in self.cuts]
        return res

class BaseExtractor:
    def extract(self, video_path: str) -> Optional[CutoutMetadata]:
        raise NotImplementedError

class EDLExtractor(BaseExtractor):
    def extract(self, video_path: str) -> Optional[CutoutMetadata]:
        """Extrai cortes de arquivos .edl (MPlayer/Kodi format)."""
        base_name = os.path.splitext(video_path)[0]
        edl_path = f"{base_name}.edl"
        
        if not os.path.exists(edl_path):
            return None

        metadata = CutoutMetadata()
        has_data = False
        
        try:
            with open(edl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        start = float(parts[0])
                        end = float(parts[1])
                        action = int(parts[2])
                        
                        # Ação 0 = Cut, Ação 3 = Commercial Break
                        if action in (0, 3):
                            if start == 0.0:
                                metadata.intro = TimeRange(start, end)
                            else:
                                metadata.cuts.append(TimeRange(start, end))
                            has_data = True
                            
            return metadata if has_data else None
        except Exception:
            return None

class ChapterExtractor(BaseExtractor):
    def __init__(self, ffprobe_bin: str = "ffprobe"):
        self.ffprobe_bin = ffprobe_bin

    def extract(self, video_path: str) -> Optional[CutoutMetadata]:
        """Lê os capítulos embutidos no MKV/MP4 usando ffprobe."""
        try:
            res = subprocess.run(
                [
                    self.ffprobe_bin,
                    "-v", "error",
                    "-show_chapters",
                    "-print_format", "json",
                    video_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            
            data = json.loads(res.stdout)
            chapters = data.get("chapters", [])
            if not chapters:
                return None
            
            metadata = CutoutMetadata()
            has_data = False
            
            intro_kws = ["intro", "opening", "abertura"]
            finish_kws = ["credits", "ending", "encerramento"]
            cut_kws = ["sponsor", "commercial", "ad", "comercial", "patrocinador"]
            
            for chap in chapters:
                title = chap.get("tags", {}).get("title", "").lower()
                start_time = float(chap.get("start_time", 0))
                end_time = float(chap.get("end_time", 0))
                
                if any(kw in title for kw in intro_kws):
                    metadata.intro = TimeRange(start_time, end_time)
                    has_data = True
                elif any(kw in title for kw in finish_kws):
                    metadata.finish = TimeRange(start_time, end_time)
                    has_data = True
                elif any(kw in title for kw in cut_kws):
                    metadata.cuts.append(TimeRange(start_time, end_time))
                    has_data = True
                    
            return metadata if has_data else None
        except Exception:
            return None

class SubtitleExtractor(BaseExtractor):
    def extract(self, video_path: str) -> Optional[CutoutMetadata]:
        """Procura legendas (.vtt, .srt) para marcadores textuais."""
        base_name = os.path.splitext(video_path)[0]
        metadata = CutoutMetadata()
        has_data = False

        for ext in [".vtt", ".srt"]:
            sub_path = f"{base_name}{ext}"
            if os.path.exists(sub_path):
                has_data |= self._parse_subtitle(sub_path, metadata)
                
        return metadata if has_data else None

    def _parse_time(self, time_str: str) -> float:
        # 00:00:00.000 ou 00:00:00,000
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return float(time_str)

    def _parse_subtitle(self, sub_path: str, metadata: CutoutMetadata) -> bool:
        has_data = False
        intro_kws = ["intro", "abertura"]
        finish_kws = ["créditos", "creditos", "encerramento"]
        
        try:
            with open(sub_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex simples para blocos SRT/VTT
            # Formato VTT/SRT comum: 00:00:00.000 --> 00:01:00.000\nTexto
            blocks = re.split(r'\n\s*\n', content)
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 2: continue
                
                time_line = next((l for l in lines if "-->" in l), None)
                if not time_line: continue
                
                t_parts = time_line.split("-->")
                start = self._parse_time(t_parts[0].strip())
                end = self._parse_time(t_parts[1].split()[0].strip()) # Remove metadados do VTT após o tempo
                
                text = " ".join(lines[lines.index(time_line)+1:]).lower()
                
                if any(kw in text for kw in intro_kws):
                    metadata.intro = TimeRange(start, end)
                    has_data = True
                elif any(kw in text for kw in finish_kws):
                    metadata.finish = TimeRange(start, end)
                    has_data = True
        except Exception:
            pass
        return has_data

class XMLNFOExtractor(BaseExtractor):
    def extract(self, video_path: str) -> Optional[CutoutMetadata]:
        """Procura XML ou NFO com tags de cortes (<epbookmark>, <edl>)."""
        base_name = os.path.splitext(video_path)[0]
        metadata = CutoutMetadata()
        has_data = False

        for ext in [".nfo", ".xml"]:
            xml_path = f"{base_name}{ext}"
            if os.path.exists(xml_path):
                try:
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    
                    # Suporte a tag <epbookmark> (Plex/Emby comum para intro/outro)
                    for bookmark in root.findall(".//epbookmark"):
                        start = float(bookmark.get("start", 0))
                        end = float(bookmark.get("end", 0))
                        b_type = bookmark.get("type", "").lower()
                        if b_type == "intro":
                            metadata.intro = TimeRange(start, end)
                            has_data = True
                        elif b_type == "credits":
                            metadata.finish = TimeRange(start, end)
                            has_data = True
                            
                    # Suporte a tag <edl> ou <chapter> se existir no esquema
                except Exception:
                    pass
                    
        return metadata if has_data else None

class CutoutManager:
    def __init__(self, ffprobe_bin: str = "ffprobe"):
        self.extractors = [
            EDLExtractor(),
            ChapterExtractor(ffprobe_bin=ffprobe_bin),
            SubtitleExtractor(),
            XMLNFOExtractor()
        ]

    def extract_all(self, video_path: str) -> Optional[Dict]:
        """Roda todos os extratores e mescla os resultados."""
        final_metadata = CutoutMetadata()
        has_any = False
        
        for extractor in self.extractors:
            meta = extractor.extract(video_path)
            if meta:
                has_any = True
                if meta.intro and not final_metadata.intro:
                    final_metadata.intro = meta.intro
                if meta.finish and not final_metadata.finish:
                    final_metadata.finish = meta.finish
                if meta.cuts:
                    final_metadata.cuts.extend(meta.cuts)
                    
        return final_metadata.to_dict() if has_any else None

class CutoutAnalyzer:
    """
    Motor de análise profunda que roda ffmpeg decodificando o arquivo para achar
    trechos de tela preta e silêncio absoluto.
    """
    
    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self.ffmpeg_bin = ffmpeg_bin

    def analyze(self, video_path: str, black_duration: float = 2.0, silence_duration: float = 2.0, 
                silence_db: str = "-50dB", progress_callback=None) -> List[Dict[str, float]]:
        """
        Retorna uma lista de dicionários com {start: float, end: float} representando
        intervalos que são simultaneamente silenciosos e com tela preta.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

        # Filtros para achar telas pretas e silêncio
        # blackdetect: d=duração mínima, pix_th=limiar de pixels não-pretos permitidos (0.00 = preto absoluto)
        # silencedetect: d=duração mínima, n=nível em dB
        cmd = [
            self.ffmpeg_bin,
            "-i", video_path,
            "-vf", f"blackdetect=d={black_duration}:pix_th=0.00",
            "-af", f"silencedetect=n={silence_db}:d={silence_duration}",
            "-f", "null",
            "-"
        ]
        
        # Regexes para capturar o log do ffmpeg
        black_start_re = re.compile(r"blackdetect.*?black_start:([0-9\.]+)")
        black_end_re = re.compile(r"blackdetect.*?black_end:([0-9\.]+)")
        silence_start_re = re.compile(r"silencedetect.*?silence_start: ([0-9\.-]+)")
        silence_end_re = re.compile(r"silencedetect.*?silence_end: ([0-9\.]+)")
        
        black_intervals = []
        silence_intervals = []
        
        current_black_start = None
        current_silence_start = None
        
        # Como pode demorar, capturamos o processo
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        
        # Lemos linha a linha conforme a IA processa
        for line in process.stderr:
            # Captura Tela Preta
            b_start_match = black_start_re.search(line)
            if b_start_match:
                current_black_start = float(b_start_match.group(1))
                
            b_end_match = black_end_re.search(line)
            if b_end_match and current_black_start is not None:
                b_end = float(b_end_match.group(1))
                black_intervals.append((current_black_start, b_end))
                current_black_start = None
                
            # Captura Silêncio
            s_start_match = silence_start_re.search(line)
            if s_start_match:
                current_silence_start = float(s_start_match.group(1))
                if current_silence_start < 0:
                    current_silence_start = 0.0
                    
            s_end_match = silence_end_re.search(line)
            if s_end_match and current_silence_start is not None:
                s_end = float(s_end_match.group(1))
                silence_intervals.append((current_silence_start, s_end))
                current_silence_start = None

        process.wait()
        
        # O pulo do gato: Intersecção. Só é um "corte" se for preto E silencioso ao mesmo tempo.
        cuts = []
        for b_start, b_end in black_intervals:
            for s_start, s_end in silence_intervals:
                # Intersecção de [b_start, b_end] e [s_start, s_end]
                i_start = max(b_start, s_start)
                i_end = min(b_end, s_end)
                
                # Se houver sobreposição e ela for maior que 1.5s
                if i_start < i_end and (i_end - i_start) >= 1.5:
                    cuts.append({"start": i_start, "end": i_end})
                    
        return cuts
