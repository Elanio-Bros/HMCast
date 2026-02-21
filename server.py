from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import os
import time
import threading
import asyncio
import atexit

from database import SessionLocal
from models import Channels
from channel import ChannelRuntime

app = FastAPI()

HLS_BASE = "hls_channels"
os.makedirs(HLS_BASE, exist_ok=True)

# Timeout configurável para aquecimento da playlist (segundos)
PLAYLIST_WARMUP_TIMEOUT = float(os.getenv("HLS_PLAYLIST_WARMUP_TIMEOUT", "15"))

channel_runtimes: dict[int, ChannelRuntime] = {}
_channel_lock = threading.Lock()

def startup_handler():
    print("[Server] Limpando arquivos HLS residuais...")
    import shutil
    try:
        if os.path.exists(HLS_BASE):
            # Remove o conteúdo, mas mantém a pasta base
            for it in os.listdir(HLS_BASE):
                it_path = os.path.join(HLS_BASE, it)
                if os.path.isdir(it_path):
                    shutil.rmtree(it_path)
                else:
                    os.remove(it_path)
    except Exception as e:
        print(f"[Server] Erro ao limpar HLS_BASE: {e}")

    print("[Server] Verificando canais ALWAYS_ON...")
    db = SessionLocal()
    try:
        always_on_channels = db.query(Channels).filter(Channels.execution_mode == "ALWAYS_ON").all()
        for ch in always_on_channels:
            print(f"[Server] Iniciando canal fixo: {ch.name}")
            ensure_channel_running(ch.id)
            # V7: Delay suave para não explodir CPU ligando tudo junto
            time.sleep(1)
    except Exception as e:
        print(f"[Server] Erro no startup_handler: {e}")
    finally:
        db.close()

def shutdown_handler():
    print("[Server] Desligando sistema... Parando canais.")
    for cid, runtime in list(channel_runtimes.items()):
        try:
            runtime.stop()
        except Exception:
            pass

# Handlers globais
atexit.register(shutdown_handler)
# Chamada de inicialização após definir handlers
# Nota: Em FastAPI, o ideal seria @app.on_event("startup"), mas como usamos atexit para shutdown,
# manteremos o padrão manual ou usaremos o lifepan do FastAPI se necessário.
async def background_warmup_worker():
    """Tarefa que pré-renderiza canais PREDICTIVE periodicamente"""
    while True:
        await asyncio.sleep(int(os.getenv("PREDICTIVE_WARMUP_INTERVAL", "300"))) # Padrao 5 min
        print("[Server] Iniciando ciclo de Warmup para canais PREDICTIVE...")
        db = SessionLocal()
        try:
            channels = db.query(Channels).filter(Channels.execution_mode == "PREDICTIVE").all()
            for ch in channels:
                # Só faz warmup se o canal NÃO estiver rodando ativamente (sem views)
                runtime = channel_runtimes.get(ch.id)
                if not runtime or not runtime.running:
                    print(f"[Server] Warmup: Pré-renderizando canal {ch.name}...")
                    # Inicia um runtime temporário (o IDLE_TIMEOUT fará ele parar após renderizar)
                    ensure_channel_running(ch.id, is_warmup=True)
        except Exception as e:
            print(f"[Server] Erro no warmup worker: {e}")
        finally:
            db.close()

@app.on_event("startup")
async def app_startup():
    # Inicia canais Always ON de forma assíncrona para não travar o loop
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, startup_handler)
    # Inicia worker de warmup
    asyncio.create_task(background_warmup_worker())

def ensure_channel_running(channel_id: int, is_warmup: bool = False) -> ChannelRuntime:
    # Evita condições de corrida ao iniciar canais
    with _channel_lock:
        runtime = channel_runtimes.get(channel_id)
        # Se ja existe e a thread está rodando, só atualiza o acesso se não for warmup
        if runtime and runtime.thread and runtime.thread.is_alive() and runtime.running:
            if not is_warmup:
                runtime.touch()
            return runtime

        # Se existe um "morto", limpa antes de criar novo
        if runtime:
            try:
                runtime.stop()
            except:
                pass

        db = SessionLocal()
        channel = db.get(Channels, channel_id)
        db.close()

        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        runtime = ChannelRuntime(channel, HLS_BASE)
        if not is_warmup:
            runtime.touch()
        
        runtime.start()
        channel_runtimes[channel_id] = runtime
        return runtime

@app.get("/channel/{channel_id}")
async def serve_channel(channel_id: int):
    ensure_channel_running(channel_id)

    return RedirectResponse(
        url=f"/channel/{channel_id}/master.m3u8",
        status_code=302
    )

@app.get("/channel/{channel_id}/status")
async def channel_status(channel_id: int):
    runtime = channel_runtimes.get(channel_id)
    if not runtime:
        return {
            "running": False,
            "ffmpeg_alive": False,
            "ffmpeg_returncode": None,
            "last_access": None,
            "since_last_access": None,
            "hls_path": None,
            "ffmpeg_log_tail": []
        }

    # Coleta últimas linhas do log
    log_path = os.path.join(HLS_BASE, f"channel_{channel_id}", "ffmpeg.log")
    tail = []
    try:
        if os.path.exists(log_path):
            with open(log_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                # lê até 16KB do final
                read_size = min(16384, size)
                f.seek(-read_size, os.SEEK_END)
                data = f.read().decode(errors="ignore")
                tail = data.strip().splitlines()[-50:]
    except Exception:
        tail = []

    proc = runtime.player.process
    ffmpeg_alive = bool(proc and proc.poll() is None)
    ffmpeg_returncode = (None if not proc else (proc.returncode if not ffmpeg_alive else None))
    since_last_access = (None if runtime.last_access is None else (time.time() - runtime.last_access))

    return {
        "running": runtime.running,
        "ffmpeg_alive": ffmpeg_alive,
        "ffmpeg_returncode": ffmpeg_returncode,
        "last_access": runtime.last_access,
        "since_last_access": since_last_access,
        "hls_path": os.path.join(HLS_BASE, f"channel_{channel_id}"),
        "ffmpeg_log_tail": tail
    }

@app.get("/channel/{channel_id}/{filename}")
async def serve_hls(channel_id: int, filename: str):
    ensure_channel_running(channel_id)
    runtime = channel_runtimes.get(channel_id)

    if not runtime:
        raise HTTPException(status_code=404)

    channel_path = os.path.join(HLS_BASE, f"channel_{channel_id}")
    # Normaliza e impede path traversal com checagem de commonpath
    base_path = os.path.realpath(os.path.abspath(channel_path))
    file_path = os.path.realpath(os.path.abspath(os.path.join(channel_path, filename)))
    try:
        common = os.path.commonpath([base_path, file_path])
    except Exception:
        raise HTTPException(status_code=400, detail="Caminho inválido")
    if common != base_path:
        raise HTTPException(status_code=400, detail="Caminho inválido")

    if filename.endswith(".m3u8"):
        start = time.time()

        def variant_ready() -> bool:
            # verifica se pelo menos um v*.m3u8 tem >= 3 segmentos
            base_dir = os.path.dirname(file_path)
            try:
                for f in os.listdir(base_dir):
                    if f.startswith("v") and f.endswith(".m3u8"):
                        p = os.path.join(base_dir, f)
                        with open(p, "r", encoding="utf-8") as fh:
                            lines = [ln.strip() for ln in fh.readlines()]
                        segs = [ln for ln in lines if ln.endswith(".ts")]
                        if len(segs) >= 3:
                            return True
            except Exception:
                pass
            return False

        while time.time() - start < PLAYLIST_WARMUP_TIMEOUT:
            # Check if file exists
            if os.path.exists(file_path):
                # Se for master, espera qualquer variante
                if os.path.basename(file_path) == "master.m3u8":
                    if variant_ready():
                        break
                else:
                    # Para variantes, checa segmentos ou se processo terminou (clipe curto)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        segments = [l for l in content.splitlines() if l.endswith(".ts")]
                        if len(segments) >= 3:
                            break
                    except:
                        pass
            
            # Se o player ja encerrou com sucesso, libera o que tiver (vídeo curto)
            if runtime.player.process and runtime.player.process.poll() is not None:
                if os.path.exists(file_path):
                    break
            
            await asyncio.sleep(0.3)

        if not os.path.exists(file_path):
            # Indica que o canal está iniciando/sem playlist ainda
            raise HTTPException(status_code=503, detail="Playlist em aquecimento")

        return FileResponse(file_path, media_type="application/vnd.apple.mpegurl")

    # Arquivos TS → comportamento normal
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404)

    return FileResponse(file_path, media_type="video/MP2T")
