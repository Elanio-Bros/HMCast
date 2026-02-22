import os
import subprocess
import shutil
from dotenv import load_dotenv
from typing import Iterable
from .database import SessionLocal
from .models import MediaItem, MediaFolder


class MediaUtils:
    SUPPORTED_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mp3", ".aac", ".ogg")

    def __init__(self):
        load_dotenv()
        # Usa variáveis de ambiente se definidas; caso contrário, usa binários no PATH do SO
        ffmpeg_env = os.getenv("FFMPEG_BIN")
        ffprobe_env = os.getenv("FFPROBE_BIN")

        # Limpeza de aspas residuais que podem vir do .env
        if ffmpeg_env: ffmpeg_env = ffmpeg_env.strip("'\"")
        if ffprobe_env: ffprobe_env = ffprobe_env.strip("'\"")

        def resolve(bin_env: str | None, fallback_name: str) -> str:
            if bin_env:
                return os.path.abspath(bin_env)
            found = shutil.which(fallback_name)
            if found:
                return os.path.abspath(found)
            return fallback_name  # deixa para o sistema resolver pelo PATH

        self.ffmpeg = resolve(ffmpeg_env, "ffmpeg")
        self.ffprobe = resolve(ffprobe_env, "ffprobe")

    # ======================================================
    # FFMPEG / FFPROBE
    # ======================================================

    def run_ffmpeg(self, args: list, stdin=None, stdout=None):
        """
        Executa o ffmpeg retornando o processo.
        Usado para streams contínuos.
        """
        popen_kwargs = {
            "stdin": stdin,
            "stdout": stdout,
            "stderr": subprocess.DEVNULL,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return subprocess.Popen([self.ffmpeg] + args, **popen_kwargs)

    def run_ffmpeg_blocking(self, args: list):
        """
        Executa ffmpeg de forma bloqueante.
        Usado para operações simples.
        """
        run_kwargs = {
            "check": True,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if os.name == "nt":
            run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.run([self.ffmpeg] + args, **run_kwargs)

    def get_media_duration(self, file_path: str) -> int:
        """
        Obtém a duração total do arquivo. Tenta primeiro pelo cabeçalho do formato
        e, se falhar, tenta pela duração do primeiro stream de vídeo/áudio.
        """
        def call_ffprobe(entries: str):
            run_kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "check": True,
            }
            if os.name == "nt":
                run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            
            res = subprocess.run(
                [
                    self.ffprobe,
                    "-v", "error",
                    "-show_entries", entries,
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path
                ],
                **run_kwargs
            )
            return res.stdout.strip()

        try:
            # Tenta pela duração do formato (rápido)
            out = call_ffprobe("format=duration")
            if out:
                return int(float(out))
            
            # Se falhar, tenta pela duração dos streams (mais lento, mas resolve alguns MKVs)
            out = call_ffprobe("stream=duration")
            if out:
                # Pode retornar várias linhas se houver vários streams, pega a primeira válida
                durations = [int(float(d)) for d in out.splitlines() if d.replace('.','',1).isdigit()]
                if durations:
                    return max(durations)
            
            return 0
        except Exception as e:
            # Em caso de erro real, não apenas silenciamos
            # Mas retornamos 0 para manter a lógica do scanner
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
        Escaneia uma pasta recursivamente e registra os arquivos no banco em lotes com tratamento de erro robusto.
        """
        root_path = self.normalize_path(root_path)
        
        with SessionLocal() as db:
            try:
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

                BATCH_SIZE = 100
                batch_count = 0
                
                print(f"[Scanner] Iniciando scan em: {root_path}")
                
                # V7: Cache de caminhos existentes em memória para evitar SELECT N+1
                existing_files = {
                    row[0] for row in db.query(MediaItem.file)
                    .filter(MediaItem.folder_id == folder.id)
                    .all()
                }
                
                # Precisamos dos objetos completos apenas se quisermos atualizar duração
                # Mas para novos arquivos, o set acima já resolve 99% da velocidade
                # Para atualização da V5, pegamos os itens sob demanda ou em cache
                items_by_file = {}
                if existing_files:
                    # Carrega apenas o necessário para atualização
                    all_items = db.query(MediaItem).filter(MediaItem.folder_id == folder.id).all()
                    items_by_file = {it.file: it for it in all_items}

                for file_path in self.iter_media_files(root_path):
                    try:
                        file_path = self.normalize_path(file_path)
                        existing_item = items_by_file.get(file_path)

                        duration = self.get_media_duration(file_path)
                        if duration <= 0:
                             print(f"[Scanner] Ignorando arquivo com duração 0/erro: {file_path}")
                             continue

                        if existing_item:
                            # Sustentabilidade V5: Atualiza duração se o arquivo mudou no disco
                            if existing_item.duration != duration:
                                print(f"[Scanner] Atualizando duração de '{existing_item.name}': {existing_item.duration}s -> {duration}s")
                                existing_item.duration = duration
                                batch_count += 1
                            continue

                        media = MediaItem(
                            name=os.path.splitext(os.path.basename(file_path))[0],
                            file=file_path,
                            duration=duration,
                            folder_id=folder.id
                        )

                        db.add(media)
                        batch_count = int(batch_count) + 1

                        if batch_count >= BATCH_SIZE:
                            db.commit()
                            print(f"[Scanner] Commit parcial de {batch_count} itens...")
                            batch_count = 0
                            
                    except Exception as e:
                        print(f"[Scanner] Erro ao processar {file_path}: {e}")
                        db.rollback()

                if batch_count > 0:
                    db.commit()
                    print(f"[Scanner] Commit final de {batch_count} itens.")

            except Exception as e:
                print(f"[Scanner] Erro fatal no scan: {e}")
                db.rollback()

    def check_dependencies(self) -> dict:
        """
        Verifica se ffmpeg e ffprobe estão instalados e retornam versão.
        """
        results = {}
        for name, exe in [("ffmpeg", self.ffmpeg), ("ffprobe", self.ffprobe)]:
            try:
                res = subprocess.run(
                    [exe, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                first_line = res.stdout.splitlines()[0]
                results[name] = {"ok": True, "version": first_line}
            except Exception as e:
                results[name] = {"ok": False, "error": str(e)}
        return results