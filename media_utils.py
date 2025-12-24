import os
import subprocess
from typing import Iterable
from database import SessionLocal
from models import MediaItem, MediaFolder

class MediaUtils:
    SUPPORTED_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mp3", ".aac", ".ogg")

    def __init__(self):
        # fixo por enquanto → depois ENV
        self.ffmpeg = "./ffmpeg/bin/ffmpeg.exe"
        self.ffprobe = "./ffmpeg/bin/ffprobe.exe"

    # -------------------------------
    # ffmpeg / ffprobe
    # -------------------------------

    def run_ffmpeg(self, args: list):
        cmd = [self.ffmpeg] + args
        subprocess.run(cmd, check=True)

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
                check=True
            )
            return int(float(result.stdout.strip()))
        except Exception as e:
            print(f"❌ Erro ao obter duração: {file_path} -> {e}")
            return 0

    # -------------------------------
    # filesystem
    # -------------------------------

    def iter_media_files(self, root_path: str) -> Iterable[str]:
        for dirpath, _, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    yield os.path.join(dirpath, file)

    def normalize_path(self, path: str) -> str:
        return os.path.normpath(path)

    def scan_media_folder(self, root_path: str):
        root_path = self.normalize_path(root_path)
        db = SessionLocal()

        # pasta raiz
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
            name = os.path.splitext(os.path.basename(file_path))[0]

            exists = (
                db.query(MediaItem)
                .filter(MediaItem.file == file_path)
                .first()
            )

            if exists:
                continue

            duration = self.get_media_duration(file_path)

            episode = MediaItem(
                name=name,
                file=file_path,
                duration=duration,
                folder_id=folder.id
            )
            db.add(episode)

        db.commit()
        db.close()