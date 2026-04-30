import os
import subprocess
import shutil
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def get_or_create_folder(self, db, file_path: str, auto_scan: bool = False):
        """
        Busca a melhor pasta raiz e cria as subpastas necessárias para manter a hierarquia.
        """
        abs_file_path = self.normalize_path(os.path.abspath(file_path))
        target_dir = self.normalize_path(os.path.dirname(abs_file_path))
        
        # 1. Encontra a melhor raiz existente
        folders = db.query(MediaFolder).all()
        best_root = None
        for folder in folders:
            norm_path = self.normalize_path(folder.path)
            if abs_file_path.lower().startswith(norm_path.lower()):
                if best_root is None or len(norm_path) > len(best_root.path):
                    best_root = folder

        # 2. Se não achou raiz nenhuma, cria a raiz baseada no diretório imediato do arquivo
        if not best_root:
            new_root = MediaFolder(
                path=target_dir,
                name=os.path.basename(target_dir),
                auto_scan=auto_scan
            )
            db.add(new_root)
            db.commit()
            db.refresh(new_root)
            return new_root

        # 3. Se achou uma raiz, precisamos garantir que as subpastas até o arquivo existem
        if self.normalize_path(best_root.path).lower() == target_dir.lower():
            return best_root

        # Caso o arquivo esteja em uma subpasta da raiz, vamos criar a hierarquia
        # Ex: Raiz=D:\Filmes, Arquivo=D:\Filmes\Acao\2024\v.mp4
        # Precisamos garantir 'Acao' e '2024'
        rel_path = os.path.relpath(target_dir, best_root.path)
        parts = rel_path.split(os.sep)
        
        current_parent_id = best_root.id
        current_path = self.normalize_path(best_root.path)
        
        for part in parts:
            if not part or part == ".": continue
            current_path = self.normalize_path(os.path.join(current_path, part))
            
            # Busca ou cria a subpasta
            subfolder = db.query(MediaFolder).filter(MediaFolder.path.ilike(current_path)).first()
            if not subfolder:
                subfolder = MediaFolder(
                    path=current_path,
                    name=part,
                    parent_id=current_parent_id,
                    auto_scan=best_root.auto_scan
                )
                db.add(subfolder)
                db.commit()
                db.refresh(subfolder)
            
            current_parent_id = subfolder.id
            
        return db.query(MediaFolder).get(current_parent_id)

    def scan_media_folder(self, root_path: str, progress_callback=None):
        """
        Porta de entrada para o scan. Prepara a raiz e inicia a recursão paralela.
        """
        root_path = self.normalize_path(os.path.abspath(root_path))
        
        with SessionLocal() as db:
            try:
                # 1. Garante a pasta raiz
                root_folder = db.query(MediaFolder).filter(MediaFolder.path.ilike(root_path)).first()
                if not root_folder:
                    root_folder = MediaFolder(path=root_path, name=os.path.basename(root_path), auto_scan=True)
                    db.add(root_folder)
                    db.commit()
                    db.refresh(root_folder)

                # 2. Contagem total para o progresso
                total_files = 0
                if progress_callback:
                    for _ in self.iter_media_files(root_path): total_files += 1
                    progress_callback(0, total_files)

                # 3. Inicia a recursão com Pool de Threads
                found_files = set()
                stats = {"count": 0, "total": total_files}
                
                # Usamos um executor com um número balanceado de threads (ex: 4 a 8)
                with ThreadPoolExecutor(max_workers=6) as executor:
                    self._recursive_scan_worker(db, root_path, root_folder.id, found_files, stats, progress_callback, executor)
                
                db.commit()

                # 4. LIMPEZA (PURGE)
                from .models import PlaylistItem
                missing_items = db.query(MediaItem).filter(
                    MediaItem.file.ilike(f"{root_path}%"),
                    ~MediaItem.file.in_(found_files)
                ).all()

                if missing_items:
                    m_ids = [m.id for m in missing_items]
                    db.query(PlaylistItem).filter(PlaylistItem.media_id.in_(m_ids)).delete(synchronize_session=False)
                    db.query(MediaItem).filter(MediaItem.id.in_(m_ids)).delete(synchronize_session=False)
                    db.commit()

            except Exception as e:
                print(f"[Scanner] ERRO NO SCAN PARALELO: {e}")
                db.rollback()
                raise e

    def _recursive_scan_worker(self, db, current_path, parent_id, found_files, stats, callback, executor):
        """
        O motor recursivo. Explora a fundo antes de focar nos arquivos.
        """
        current_path = self.normalize_path(current_path)
        file_tasks = {}

        try:
            # 1. Lista tudo o que tem na pasta atual
            with os.scandir(current_path) as it:
                entries = list(it)

            # 2. SEPARA E PROCESSA PASTAS (Mergulha primeiro)
            for entry in entries:
                if entry.is_dir():
                    full_path = self.normalize_path(entry.path)
                    
                    # Garante a subpasta no banco
                    subfolder = db.query(MediaFolder).filter(MediaFolder.path.ilike(full_path)).first()
                    if not subfolder:
                        subfolder = MediaFolder(
                            path=full_path,
                            name=entry.name,
                            parent_id=parent_id,
                            auto_scan=True # Herdado ou padrão
                        )
                        db.add(subfolder)
                        db.commit()
                        db.refresh(subfolder)
                    
                    # RECURSÃO: Mergulha na subpasta
                    self._recursive_scan_worker(db, full_path, subfolder.id, found_files, stats, callback, executor)

            # 3. PROCESSA ARQUIVOS DA PASTA ATUAL (Depois de ter mergulhado nas subpastas)
            for entry in entries:
                if entry.is_file() and entry.name.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    full_path = self.normalize_path(entry.path)
                    # Adiciona ao pool de processamento
                    future = executor.submit(self.get_media_duration, full_path)
                    file_tasks[future] = (full_path, entry.name)

            # 4. Coleta resultados dos arquivos
            for future in as_completed(file_tasks):
                f_path, f_name = file_tasks[future]
                duration = future.result()
                
                if duration > 0:
                    found_files.add(f_path)
                    item = db.query(MediaItem).filter(MediaItem.file.ilike(f_path)).first()
                    
                    if not item:
                        item = MediaItem(name=os.path.splitext(f_name)[0], file=f_path, duration=duration, folder_id=parent_id)
                        db.add(item)
                    else:
                        if item.folder_id != parent_id or item.duration != duration:
                            item.folder_id = parent_id
                            item.duration = duration
                    
                    # Atualiza progresso
                    stats["count"] += 1
                    if callback:
                        callback(stats["count"], stats["total"])
                    
                    # Commit em pequenos lotes
                    if stats["count"] % 10 == 0:
                        db.commit()

        except PermissionError:
            print(f"[Scanner] Sem permissão: {current_path}")
        except Exception as e:
            print(f"[Scanner] Erro em {current_path}: {e}")

    def health_check_all_folders(self):
        """
        Verifica todos os MediaItems do banco. Se o arquivo físico não existir, remove do banco.
        Útil para pastas com auto_scan=False que não entram no scan recursivo.
        """
        print("[Scanner] Iniciando Health Check global...")
        with SessionLocal() as db:
            from .models import PlaylistItem
            all_items = db.query(MediaItem).all()
            missing_ids = []
            
            for item in all_items:
                if not os.path.exists(item.file):
                    missing_ids.append(item.id)
            
            if missing_ids:
                print(f"[Scanner] Health Check: Removendo {len(missing_ids)} itens órfãos...")
                db.query(PlaylistItem).filter(PlaylistItem.media_id.in_(missing_ids)).delete(synchronize_session=False)
                db.query(MediaItem).filter(MediaItem.id.in_(missing_ids)).delete(synchronize_session=False)
                db.commit()
            
            print("[Scanner] Health Check concluído.")

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