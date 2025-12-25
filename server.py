from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

from database import SessionLocal
from models import Channels
from channel import ChannelRuntime

app = FastAPI()

HLS_BASE = "hls_channels"
os.makedirs(HLS_BASE, exist_ok=True)

# Mantém os runtimes vivos
channel_runtimes: dict[int, ChannelRuntime] = {}


# ----------------------------------------
# STARTUP — inicia todos os canais
# ----------------------------------------
@app.on_event("startup")
def start_channels():
    print("🚀 Iniciando canais...")

    db = SessionLocal()
    channels = db.query(Channels).all()

    for channel in channels:
        runtime = ChannelRuntime(channel)
        runtime.start_thread()
        channel_runtimes[channel.id] = runtime

        print(f"✅ Canal {channel.id} iniciado")

    db.close()


# ----------------------------------------
# ENDPOINT HLS
# ----------------------------------------
@app.get("/channel/{channel_id}/{filename}")
async def serve_hls(channel_id: int, filename: str):
    runtime = channel_runtimes.get(channel_id)

    if not runtime:
        raise HTTPException(status_code=404, detail="Canal não encontrado")

    path = os.path.join(HLS_BASE, f"channel_{channel_id}", filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404)

    if filename.endswith(".m3u8"):
        return FileResponse(path, media_type="application/vnd.apple.mpegurl")

    return FileResponse(path, media_type="video/MP2T")