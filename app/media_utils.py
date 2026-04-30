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

    def get_or_create_folder(self, db, file_path: str, auto_scan: bool = False):
        """
        Busca a melhor pasta raiz cadastrada para o arquivo.
        Se o arquivo estiver dentro de uma pasta já cadastrada, retorna ela.
        Caso contrário, cria uma nova pasta raiz baseada no diretório pai.
        """
        abs_file_path = self.normalize_path(os.path.abspath(file_path))
        file_dir = os.path.dirname(abs_file_path)
        
        # Busca todas as pastas e ordena pela maior string (melhor correspondência)
        folders = db.query(MediaFolder).all()
        best_match = None
        
        for folder in folders:
            norm_folder_path = self.normalize_path(folder.path)
            if abs_file_path.startswith(norm_folder_path):
                if best_match is None or len(norm_folder_path) > len(best_match.path):
                    best_match = folder
        
        if best_match:
            return best_match
            
        # Se não achou nenhuma raiz, cria uma nova para o diretório pai
        new_folder = MediaFolder(
            path=file_dir,
            name=os.path.basename(file_dir),
            auto_scan=auto_scan
        )
        db.add(new_folder)
        db.commit()
        db.refresh(new_folder)
        return new_folder

    def scan_media_folder(self, root_path: str, progress_callback=None):
        """
        Escaneia uma pasta recursivamente com suporte a callback de progresso.
        Garante a criação correta da hierarquia e evita erros de integridade.
        """
        root_path = self.normalize_path(os.path.abspath(root_path))
        
        with SessionLocal() as db:
            try:
                # 1. Garante a pasta raiz (Sempre normalizada)
                root_folder = db.query(MediaFolder).filter(MediaFolder.path == root_path).first()
                if not root_folder:
                    root_folder = MediaFolder(
                        path=root_path,
                        name=os.path.basename(root_path),
                        auto_scan=True
                    )
                    db.add(root_folder)
                    db.commit()
                    db.refresh(root_folder)

                # 2. Contagem para o progresso
                total_files = 0
                if progress_callback:
                    for _ in self.iter_media_files(root_path):
                        total_files += 1
                    progress_callback(0, total_files)

                # 3. Cache de pastas (Chave sempre normalizada e minúscula para Windows)
                folder_cache = { root_path.lower(): root_folder.id }
                found_files = set()
                processed_count = 0
                BATCH_SIZE = 50
                batch_count = 0

                print(f"[Scanner] Iniciando scan em: {root_path}")

                for dirpath, dirnames, filenames in os.walk(root_path):
                    dirpath = self.normalize_path(dirpath)
                    dirpath_lower = dirpath.lower()
                    
                    # Garante que a pasta atual existe no banco e no cache
                    current_folder_id = folder_cache.get(dirpath_lower)
                    
                    if not current_folder_id:
                        # Se não está no cache, busca no banco
                        folder = db.query(MediaFolder).filter(MediaFolder.path == dirpath).first()
                        if not folder:
                            # Se não existe no banco, cria. Busca o pai.
                            parent_path = self.normalize_path(os.path.dirname(dirpath))
                            parent_id = folder_cache.get(parent_path.lower())
                            
                            # Se o pai não está no cache, busca no banco
                            if not parent_id:
                                parent_folder = db.query(MediaFolder).filter(MediaFolder.path == parent_path).first()
                                parent_id = parent_folder.id if parent_folder else root_folder.id
                            
                            folder = MediaFolder(
                                path=dirpath, 
                                name=os.path.basename(dirpath), 
                                parent_id=parent_id, 
                                auto_scan=root_folder.auto_scan
                            )
                            db.add(folder)
                            db.commit()
                            db.refresh(folder)
                        
                        current_folder_id = folder.id
                        folder_cache[dirpath_lower] = current_folder_id

                    # Processa arquivos
                    for fname in filenames:
                        if not fname.lower().endswith(self.SUPPORTED_EXTENSIONS):
                            continue
                            
                        file_path = self.normalize_path(os.path.join(dirpath, fname))
                        found_files.add(file_path)
                        
                        # Verifica item existente
                        item = db.query(MediaItem).filter(MediaItem.file == file_path).first()
                        duration = self.get_media_duration(file_path)
                        
                        if duration > 0:
                            if not item:
                                item = MediaItem(
                                    name=os.path.splitext(fname)[0], 
                                    file=file_path, 
                                    duration=duration, 
                                    folder_id=current_folder_id
                                )
                                db.add(item)
                                batch_count += 1
                            else:
                                # Atualiza se mudou de pasta ou duração
                                if item.folder_id != current_folder_id or item.duration != duration:
                                    item.folder_id = current_folder_id
                                    item.duration = duration
                                    batch_count += 1

                        processed_count += 1
                        if progress_callback:
                            progress_callback(processed_count, total_files)

                        if batch_count >= BATCH_SIZE:
                            db.commit()
                            batch_count = 0

                db.commit()

                # 4. LIMPEZA (PURGE)
                from .models import PlaylistItem
                all_folders_ids = list(folder_cache.values())
                missing_items = db.query(MediaItem).filter(
                    MediaItem.folder_id.in_(all_folders_ids), 
                    ~MediaItem.file.in_(found_files)
                ).all()

                if missing_items:
                    m_ids = [m.id for m in missing_items]
                    db.query(PlaylistItem).filter(PlaylistItem.media_id.in_(m_ids)).delete(synchronize_session=False)
                    db.query(MediaItem).filter(MediaItem.id.in_(m_ids)).delete(synchronize_session=False)
                    db.commit()

            except Exception as e:
                print(f"[Scanner] ERRO NO SCAN: {e}")
                db.rollback()
                raise e # Propaga o erro para o worker saber que falhou

                # Remove pastas vazias ou que não existem mais (opcional, mas bom para manter limpo)
                # (Apenas pastas que estão sob a root_path e não foram encontradas no walk)
                # Nota: found_folders contém IDs. Precisamos dos IDs que NÃO estão lá.
                # Mas para simplificar, vamos focar em remover mídias.

            except Exception as e:
                print(f"[Scanner] Erro fatal no scan: {e}")
                db.rollback()

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