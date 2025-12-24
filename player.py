import os
import subprocess
class Player:
    def generate_hls(self, input_file: str, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        qualities = [
            ("1080", "5000k"),
            ("720", "2500k"),
            ("480", "1000k")
        ]
        streams = []

        for res, br in qualities:
            playlist_name = f"{res}p.m3u8"
            output_path = os.path.join(output_dir, playlist_name)
            cmd = [
                "ffmpeg",
                "-y",  # sobrescrever se já existir
                "-i", input_file,
                "-vf", f"scale=-2:{res}",
                "-c:v", "libx264",
                "-b:v", br,
                "-c:a", "aac",
                "-ar", "48000",
                "-ac", "2",
                "-f", "hls",
                "-hls_time", "4",
                "-hls_playlist_type", "vod",
                output_path
            ]
            subprocess.run(cmd, check=True)
            streams.append((res, br, playlist_name))

        # Criar playlist mestre
        master_path = os.path.join(output_dir, "master.m3u8")
        with open(master_path, "w") as f:
            f.write("#EXTM3U\n")
            for res, br, pl in streams:
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={int(br[:-1])*1000},RESOLUTION={res}x{int(int(res)*16/9)}\n{pl}\n")
        return master_path

    def play_off_air(self, duration: int = 5, off_air_image: str = "off_air.png"):
        cmd = []
        if off_air_image and os.path.exists(off_air_image):
            cmd = [
                "ffmpeg",
                "-loop", "1",
                "-i", off_air_image,
                "-t", str(duration),
                "-f", "mpegts",
                "pipe:1"
            ]
        else:
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c=black:s=1280x720:d={duration}",
                "-f", "mpegts",
                "pipe:1"
            ]
        subprocess.run(cmd, check=True)
