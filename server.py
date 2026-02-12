from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import os
import time
import threading

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

def ensure_channel_running(channel_id: int) -> ChannelRuntime:
    # Evita condições de corrida ao iniciar canais
    with _channel_lock:
        runtime = channel_runtimes.get(channel_id)
        if runtime and runtime.thread.is_alive():
            runtime.touch()
            return runtime

        db = SessionLocal()
        channel = db.get(Channels, channel_id)
        db.close()

        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        runtime = ChannelRuntime(channel)
        # Armazena antes de iniciar para evitar duplicatas em corrida
        channel_runtimes[channel_id] = runtime
        runtime.start()
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
            "last_access": None,
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

    return {
        "running": runtime.running,
        "ffmpeg_alive": bool(runtime.player.process and runtime.player.process.poll() is None),
        "last_access": runtime.last_access,
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
    # Normaliza e impede path traversal
    file_path = os.path.normpath(os.path.join(channel_path, filename))
    if not file_path.startswith(os.path.abspath(channel_path)):
        raise HTTPException(status_code=400, detail="Caminho inválido")

    if filename.endswith(".m3u8"):
        start = time.time()

        while time.time() - start < PLAYLIST_WARMUP_TIMEOUT:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    content = ""

                segments = [
                    line for line in content.splitlines()
                    if line.endswith(".ts")
                ]

                if len(segments) >= 3:
                    break

            time.sleep(0.3)

        if not os.path.exists(file_path):
            # Indica que o canal está iniciando/sem playlist ainda
            raise HTTPException(status_code=503, detail="Playlist em aquecimento")

        return FileResponse(file_path, media_type="application/vnd.apple.mpegurl")

    # Arquivos TS → comportamento normal
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404)

    return FileResponse(file_path, media_type="video/MP2T")
