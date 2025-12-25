import os
import subprocess
import signal
from media_utils import MediaUtils


class Player:
    def __init__(self):
        self.media = MediaUtils()
        self.process: subprocess.Popen | None = None
        self.current_file = None

    def stop(self):
        """Finaliza o processo do ffmpeg se estiver rodando"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()

        self.process = None
        self.current_file = None

    def start(
        self,
        input_file: str,
        output_dir: str,
        start_time: float = 0.0
    ):
        """
        Inicia o streaming HLS com múltiplas resoluções
        """
        self.stop()

        os.makedirs(output_dir, exist_ok=True)
        self.current_file = input_file

        cmd = [
            self.media.ffmpeg,

            "-y",
            "-ss", str(start_time),
            "-i", input_file,

            # ---------- VIDEO FILTERS ----------
            "-filter_complex",
            (
                "[0:v]split=3[v1080][v720][v480];"
                "[v1080]scale=-2:1080[v1080out];"
                "[v720]scale=-2:720[v720out];"
                "[v480]scale=-2:480[v480out]"
            ),

            # ---------- MAPPING ----------
            "-map", "[v1080out]", "-map", "0:a:0",
            "-map", "[v720out]",  "-map", "0:a:0",
            "-map", "[v480out]",  "-map", "0:a:0",

            # ---------- VIDEO ----------
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-profile:v", "main",
            "-pix_fmt", "yuv420p",

            "-b:v:0", "5000k",
            "-b:v:1", "2500k",
            "-b:v:2", "1000k",

            # ---------- AUDIO ----------
            "-c:a", "aac",
            "-ar", "48000",
            "-ac", "2",

            # ---------- HLS ----------
            "-f", "hls",
            "-hls_time", "4",
            "-hls_list_size", "6",
            "-hls_delete_threshold", "1",
            "-hls_flags", "delete_segments+append_list+independent_segments+program_date_time",

            "-hls_segment_filename",
            os.path.join(output_dir, "v%v_seg_%03d.ts"),

            "-master_pl_name", "master.m3u8",

            "-var_stream_map",
            "v:0,a:0,name:1080p v:1,a:1,name:720p v:2,a:2,name:480p",

            os.path.join(output_dir, "v%v.m3u8")
        ]

        print("[Player] Iniciando FFmpeg...")
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None