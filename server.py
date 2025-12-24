import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="ErsatzTV HLS Server")

HLS_BASE_FOLDER = "hls_channels"

if not os.path.exists(HLS_BASE_FOLDER):
    os.makedirs(HLS_BASE_FOLDER)

app.mount("/hls", StaticFiles(directory=HLS_BASE_FOLDER), name="hls")

@app.get("/channel/{channel_id}/episode/{episode_id}/master.m3u8")
async def get_master_playlist(channel_id: int, episode_id: int):
    file_path = os.path.join(
        HLS_BASE_FOLDER,
        f"channel_{channel_id}",
        f"episode_{episode_id}",
        "master.m3u8"
    )
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Master playlist não encontrada")
    return FileResponse(file_path, media_type="application/vnd.apple.mpegurl")

@app.get("/channel/{channel_id}/episode/{episode_id}/{segment_name}")
async def get_ts_segment(channel_id: int, episode_id: int, segment_name: str):
    file_path = os.path.join(
        HLS_BASE_FOLDER,
        f"channel_{channel_id}",
        f"episode_{episode_id}",
        segment_name
    )
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Segmento não encontrado")
    return FileResponse(file_path, media_type="video/MP2T")

@app.get("/channels")
async def list_channels():
    channels = []
    for channel_folder in os.listdir(HLS_BASE_FOLDER):
        channels.append(channel_folder)
    return {"channels": channels}

@app.get("/channel/{channel_id}/episodes")
async def list_episodes(channel_id: int):
    channel_folder = os.path.join(HLS_BASE_FOLDER, f"channel_{channel_id}")
    if not os.path.exists(channel_folder):
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    episodes = [d for d in os.listdir(channel_folder) if os.path.isdir(os.path.join(channel_folder, d))]
    return {"episodes": episodes}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
