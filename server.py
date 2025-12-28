from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse,RedirectResponse
import os
import time

from database import SessionLocal
from models import Channels
from channel import ChannelRuntime

app = FastAPI()

HLS_BASE = "hls_channels"
os.makedirs(HLS_BASE, exist_ok=True)

channel_runtimes: dict[int, ChannelRuntime] = {}

def ensure_channel_running(channel_id: int) -> ChannelRuntime:
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

@app.get("/channel/{channel_id}/{filename}")
async def serve_hls(channel_id: int, filename: str):
    ensure_channel_running(channel_id)
    runtime = channel_runtimes.get(channel_id)

    if not runtime:
        raise HTTPException(status_code=404)

    channel_path = os.path.join(HLS_BASE, f"channel_{channel_id}")
    file_path = os.path.join(channel_path, filename)

    if filename.endswith(".m3u8"):
        timeout = 10  # segundos
        start = time.time()

        while time.time() - start < timeout:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                segments = [
                    line for line in content.splitlines()
                    if line.endswith(".ts")
                ]

                if len(segments) >= 3:
                    break

            time.sleep(0.3)

        # Se ainda não existir → 404
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404)

        return FileResponse(
            file_path,
            media_type="application/vnd.apple.mpegurl"
        )

    # Arquivos TS → comportamento normal
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404)

    return FileResponse(file_path, media_type="video/MP2T")
