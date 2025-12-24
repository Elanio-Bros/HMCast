import os
from media_utils import MediaUtils

class Player:
    def __init__(self):
        self.media = MediaUtils()

    def generate_hls(self, input_file: str, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)

        args = [
            "-y",
            "-i", input_file,

            # ===== FILTER COMPLEX =====
            "-filter_complex",
            (
                "[0:v]split=3[v1080][v720][v480];"
                "[v1080]scale=-2:1080[v1080out];"
                "[v720]scale=-2:720[v720out];"
                "[v480]scale=-2:480[v480out]"
            ),

            # ===== MAPS =====
            "-map", "[v1080out]", "-map", "0:a",
            "-map", "[v720out]",  "-map", "0:a",
            "-map", "[v480out]",  "-map", "0:a",

            # ===== CODECS =====
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-profile:v", "main",
            "-crf", "20",

            "-c:a", "aac",
            "-ar", "48000",
            "-ac", "2",

            # ===== BITRATES =====
            "-b:v:0", "5000k",
            "-b:v:1", "2500k",
            "-b:v:2", "1000k",

            # ===== HLS =====
            "-f", "hls",
            "-hls_time", "4",
            "-hls_playlist_type", "event",
            "-hls_flags", "independent_segments+delete_segments",
            "-hls_segment_filename",
            os.path.join(output_dir, "v%v_seg_%03d.ts"),

            # ===== MASTER PLAYLIST =====
            "-master_pl_name", "master.m3u8",

            # ===== STREAM MAP =====
            "-var_stream_map",
            "v:0,a:0,name:1080p v:1,a:1,name:720p v:2,a:2,name:480p",

            os.path.join(output_dir, "v%v.m3u8")
        ]

        self.media.run_ffmpeg(args)
        return os.path.join(output_dir, "master.m3u8")

    def play_off_air(self, duration: int = 5, image_path: str | None = None):
        if image_path and os.path.exists(image_path):
            args = [
                "-loop", "1",
                "-i", image_path,
                "-t", str(duration),
                "-f", "mpegts",
                "pipe:1"
            ]
        else:
            args = [
                "-f", "lavfi",
                "-i", f"color=c=black:s=1280x720:d={duration}",
                "-f", "mpegts",
                "pipe:1"
            ]

        self.media.run_ffmpeg(args)