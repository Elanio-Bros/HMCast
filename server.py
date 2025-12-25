# server.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
from channel import ChannelRuntime
from database import SessionLocal
from models import Channels

app = FastAPI()

HLS_BASE = "hls_channels"
os.makedirs(HLS_BASE, exist_ok=True)

channel_runtimes = {}

def get_runtime(channel_id: int):
    if channel_id in channel_runtimes:
        return channel_runtimes[channel_id]

    db = SessionLocal()
    channel = db.query(Channels).filter(Channels.id == channel_id).first()
    db.close()

    if not channel:
        return None

    runtime = ChannelRuntime(channel)
    channel_runtimes[channel_id] = runtime
    return runtime

@app.get("/channel/{channel_id}/{filename}")
async def serve_hls(channel_id: int, filename: str):
    runtime = get_runtime(channel_id)
    if not runtime:
        raise HTTPException(404)

    # Inicia o live HLS on-demand
    runtime.get_current_master()

    path = os.path.join("hls_channels", f"channel_{channel_id}", filename)
    if not os.path.exists(path):
        raise HTTPException(404)

    if filename.endswith(".m3u8"):
        return FileResponse(path, media_type="application/vnd.apple.mpegurl")
    return FileResponse(path, media_type="video/MP2T")
