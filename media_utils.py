import os
import subprocess
from typing import Iterable
from database import SessionLocal
from models import MediaItem, MediaFolder


class MediaUtils:
    SUPPORTED_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mp3", ".aac", ".ogg")

    def __init__(self):
        # Permite sobrescrever caminhos via variáveis de ambiente
        ffmpeg_env = os.getenv("FFMPEG_BIN")
        ffprobe_env = os.getenv("FFPROBE_BIN")
        self.ffmpeg = os.path.abspath(ffmpeg_env) if ffmpeg_env else os.path.abspath("./ffmpeg/bin/ffmpeg.exe")
        self.ffprobe = os.path.abspath(ffprobe_env) if ffprobe_env else os.path.abspath("./ffmpeg/bin/ffprobe.exe")

    # ======================================================
    # FFMPEG / FFPROBE
    # ======================================================

    def run_ffmpeg(self, args: list, stdin=None, stdout=None):
        """
        Executa o ffmpeg retornando o processo.
        Usado para streams contínuos.
        """
        return subprocess.Popen(
            [self.ffmpeg] + args,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def run_ffmpeg_blocking(self, args: list):
        """
        Executa ffmpeg de forma bloqueante.
        Usado para operações simples.
        """
        subprocess.run(
            [self.ffmpeg] + args,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def get_media_duration(self, file_path: str) -> int:
        try:
            result = subprocess.run(
                [
                    self.ffprobe,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return int(float(result.stdout.strip()))
        except Exception:
            return 0

    # ======================================================
    # FILESYSTEM / MEDIA SCAN
    # ======================================================

    def iter_media_files(self, root_path: str) -> Iterable[str]:
        for dirpath, _, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    yield os.path.join(dirpath, file)

    def normalize_path(self, path: str) -> str:
        return os.path.normpath(path)

    def scan_media_folder(self, root_path: str):
        """
        Escaneia uma pasta e registra os arquivos no banco.
        """
        root_path = self.normalize_path(root_path)
        db = SessionLocal()

        folder = (
            db.query(MediaFolder)
            .filter(MediaFolder.path == root_path)
            .first()
        )

        if not folder:
            folder = MediaFolder(
                path=root_path,
                name=os.path.basename(root_path)
            )
            db.add(folder)
            db.commit()
            db.refresh(folder)

        for file_path in self.iter_media_files(root_path):
            file_path = self.normalize_path(file_path)

            exists = (
                db.query(MediaItem)
                .filter(MediaItem.file == file_path)
                .first()
            )

            if exists:
                continue

            duration = self.get_media_duration(file_path)

            media = MediaItem(
                name=os.path.splitext(os.path.basename(file_path))[0],
                file=file_path,
                duration=duration,
                folder_id=folder.id
            )

            db.add(media)

        db.commit()
        db.close()