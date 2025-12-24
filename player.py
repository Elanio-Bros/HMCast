# player.py
import subprocess

class Player:
    def stream_segments(self, file_path: str, segments, offset: float = 0):
        """
        Stream contínuo via ffmpeg respeitando cortes.
        segments: lista de tuplas (start, end) em segundos
        offset: tempo inicial dentro do episódio
        """
        for start, end in segments:
            seg_start = start + offset
            seg_duration = end - seg_start
            cmd = [
                "ffmpeg",
                "-ss", str(seg_start),
                "-i", file_path,
                "-t", str(seg_duration),
                "-c:v", "copy",
                "-c:a", "aac",
                "-f", "mpegts",
                "pipe:1"
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                data = process.stdout.read(1024*8)
                if not data:
                    break
                yield data
            process.stdout.close()
            process.wait()
            offset = 0  # só aplicável no primeiro segmento do episódio
