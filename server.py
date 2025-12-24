import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import threading
from database import SessionLocal
from models import Channels
from channel import ChannelRuntime

app = FastAPI(title="ErsatzTV Minimal HLS Server")

HLS_BASE_FOLDER = "hls_channels"
if not os.path.exists(HLS_BASE_FOLDER):
    os.makedirs(HLS_BASE_FOLDER)

app.mount("/hls", StaticFiles(directory=HLS_BASE_FOLDER), name="hls")

active_channels = {}

@app.get("/channel/{channel_id}")
async def get_channel_master(channel_id: int):
    channel_folder = os.path.join(HLS_BASE_FOLDER, f"channel_{channel_id}", "current")
    master_path = os.path.join(channel_folder, "master.m3u8")

    if channel_id not in active_channels:
        db = SessionLocal()
        channel = db.query(Channels).filter(Channels.id == channel_id).first()
        db.close()
        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        runtime = ChannelRuntime(channel)
        t = threading.Thread(target=runtime.run, daemon=True)
        t.start()
        active_channels[channel_id] = runtime

    import time
    timeout = 5
    while not os.path.exists(master_path) and timeout > 0:
        time.sleep(0.5)
        timeout -= 0.5

    if not os.path.exists(master_path):
        raise HTTPException(status_code=404, detail="Master playlist ainda não disponível")

    return FileResponse(master_path, media_type="application/vnd.apple.mpegurl")

@app.get("/channels")
async def list_channels():
    db = SessionLocal()
    channels = db.query(Channels).all()
    db.close()
    return {"channels": [c.id for c in channels]}

@app.get("/channel/{channel_id}/episodes")
async def list_episodes(channel_id: int):
    channel_folder = os.path.join(HLS_BASE_FOLDER, f"channel_{channel_id}")
    if not os.path.exists(channel_folder):
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    episodes = [d for d in os.listdir(channel_folder) if os.path.isdir(os.path.join(channel_folder, d))]
    return {"episodes": episodes}