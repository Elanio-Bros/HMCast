import os
import subprocess
import time
from media_utils import MediaUtils


class Player:
    def __init__(self):
        self.media = MediaUtils()
        self.process = None
        self.err_fd = None

    def start(self, input_file: str, output_dir: str, start_time: float = 0, duration: float = 0):
        # Encerrar qualquer processo anterior
        self.stop()
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.exists(input_file):
            print(f"[Player] Arquivo de entrada não existe: {input_file}")
            return

        # Log de erro por canal/saída
        ffmpeg_log = os.path.join(output_dir, "ffmpeg.log")
        self.err_fd = open(ffmpeg_log, "ab", buffering=0)

        cmd = [
            self.media.ffmpeg,
            "-re", "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", input_file,
            "-threads", "2",

            # VIDEO FILTERS
            "-filter_complex",
            "[0:v]split=3[v1080][v720][v480];"
            "[v1080]scale=-2:1080[v1080out];"
            "[v720]scale=-2:720[v720out];"
            "[v480]scale=-2:480[v480out]",

            # MAPPING (um único áudio 0:a:0 para todas as variantes)
            "-map", "[v1080out]", "-map", "0:a:0",
            "-map", "[v720out]",  "-map", "0:a:0",
            "-map", "[v480out]",  "-map", "0:a:0",

            # VIDEO
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-profile:v", "main",
            "-pix_fmt", "yuv420p",
            "-crf", "20",
            "-tune", "zerolatency",
            "-bf", "1",
            "-sc_threshold", "0",
            "-g", "50",
            "-keyint_min", "50",

            # AUDIO
            "-c:a", "aac",
            "-ar", "48000",
            "-ac", "2",

            # BITRATE por variante
            "-b:v:0", "5000k",
            "-b:v:1", "2500k",
            "-b:v:2", "1000k",

            # HLS
            "-f", "hls",
            "-segment_list_flags", "+live+append_list",
            "-hls_time", "5",
            "-hls_list_size", "10",
            "-hls_delete_threshold", "5",
            "-hls_flags", "delete_segments+append_list+program_date_time+omit_endlist+discont_start",
            "-hls_allow_cache", "0",

            "-hls_segment_filename", os.path.join(output_dir, "v%v_seg_%03d.ts"),
            "-master_pl_name", "master.m3u8",
            "-var_stream_map", "v:0,a:0,name:1080p v:1,a:0,name:720p v:2,a:0,name:480p",
            os.path.join(output_dir, "v%v.m3u8")
        ]

        print(f"[Player] Iniciando FFmpeg para {input_file}...")
        self.process = subprocess.Popen(cmd, stderr=self.err_fd)
        # Checagem de falha rápida
        time.sleep(1)
        if self.process.poll() is not None and self.process.returncode != 0:
            print(f"[Player] FFmpeg encerrou imediatamente com código {self.process.returncode}")
            try:
                if self.err_fd:
                    self.err_fd.flush()
                    self.err_fd.close()
            except Exception:
                pass
            self.err_fd = None
            self.process = None
            return
        print(f"[Player] FFmpeg iniciado: {input_file}")

    def stop(self):
        if self.process and self.process.poll() is None:
            print("[Player] Encerrando FFmpeg (terminate)...")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                print("[Player] Forçando encerramento (kill)...")
                try:
                    self.process.kill()
                except Exception:
                    pass
            finally:
                try:
                    if self.err_fd:
                        self.err_fd.close()
                except Exception:
                    pass
                self.err_fd = None
                self.process = None
