# media_utils.py
import os
import subprocess
from models import Episode, MediaFolder
from database import SessionLocal

def get_media_duration(file_path: str) -> int:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = float(result.stdout.strip())
        return int(duration)
    except Exception as e:
        print(f"Erro ao obter duração de {file_path}: {e}")
        return 0

def scan_media_folder(root_path: str):
    db = SessionLocal()
    supported_extensions = [".mp4", ".mkv", ".avi", ".mp3", ".aac", ".ogg"]

    folder = db.query(MediaFolder).filter(MediaFolder.path == root_path).first()
    if not folder:
        folder = MediaFolder(path=root_path, name=os.path.basename(root_path))
        db.add(folder)
        db.commit()
        db.refresh(folder)

    for dirpath, dirnames, files in os.walk(root_path):
        for f in files:
            if any(f.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(dirpath, f)
                name = os.path.splitext(f)[0]

                exists = db.query(Episode).filter(Episode.file == file_path).first()
                if not exists:
                    duration = get_media_duration(file_path)
                    episode = Episode(
                        name=name,
                        file=file_path,
                        duration=duration,
                        folder_id=folder.id
                    )
                    db.add(episode)
    db.commit()
