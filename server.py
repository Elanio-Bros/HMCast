from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import os
import time
import asyncio
import atexit

import engine
from engine import HLS_BASE, ensure_channel_running, channel_runtimes

app = FastAPI()

@app.on_event("startup")
async def app_startup():
    # Inicia lógica de core da engine em thread separada
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, engine.startup_logic)
    # Inicia worker de warmup da engine
    asyncio.create_task(engine.background_warmup_worker())

@app.on_event("shutdown")
async def app_shutdown():
    engine.shutdown_logic()

# Registro atexit redundante para segurança extra no Windows
atexit.register(engine.shutdown_logic)

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
    base_path = os.path.realpath(os.path.abspath(channel_path))
    file_path = os.path.realpath(os.path.abspath(os.path.join(channel_path, filename)))
    
    try:
        common = os.path.commonpath([base_path, file_path])
        if common != base_path:
            raise HTTPException(status_code=400, detail="Caminho inválido")
    except Exception:
        raise HTTPException(status_code=400, detail="Caminho inválido")

    if filename.endswith(".m3u8"):
        start = time.time()

        def variant_ready() -> bool:
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

        while time.time() - start < engine.PLAYLIST_WARMUP_TIMEOUT:
            if os.path.exists(file_path):
                if os.path.basename(file_path) == "master.m3u8":
                    if variant_ready():
                        break
                else:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        segments = [l for l in content.splitlines() if l.endswith(".ts")]
                        if len(segments) >= 3:
                            break
                    except:
                        pass
            
            if runtime.player.process and runtime.player.process.poll() is not None:
                if os.path.exists(file_path):
                    break
            
            await asyncio.sleep(0.3)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=503, detail="Playlist em aquecimento")

        return FileResponse(file_path, media_type="application/vnd.apple.mpegurl")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404)

    return FileResponse(file_path, media_type="video/MP2T")
