import os
import threading
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from database import SessionLocal
from models import Channels
from channel import ChannelRuntime

app = FastAPI(title="ErsatzTV Minimal HLS Server")

HLS_BASE_FOLDER = "hls_channels"
CHANNEL_TIMEOUT = 5 * 60  # 5 minutos

if not os.path.exists(HLS_BASE_FOLDER):
    os.makedirs(HLS_BASE_FOLDER)

app.mount("/hls", StaticFiles(directory=HLS_BASE_FOLDER), name="hls")

# Dicionários globais para canais on-demand
active_channels = {}
last_access = {}

@app.get("/channel/{channel_id}")
async def get_channel_master(channel_id: int):
    channel_folder = os.path.join(HLS_BASE_FOLDER, f"channel_{channel_id}", "current")
    master_path = os.path.join(channel_folder, "master.m3u8")

    now_ts = time.time()
    last_access[channel_id] = now_ts  # atualiza último acesso

    # Verifica se o canal está ativo; se não, inicia
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

    # Espera o master.m3u8 gerar
    timeout = 5
    while not os.path.exists(master_path) and timeout > 0:
        time.sleep(0.5)
        timeout -= 0.5

    if not os.path.exists(master_path):
        raise HTTPException(status_code=404, detail="Master playlist ainda não disponível")

    return FileResponse(master_path, media_type="application/vnd.apple.mpegurl")
