# server.py
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from datetime import datetime
from channel import ChannelRuntime
from models import Channels, Playlist
from database import SessionLocal
from player import Player

app = FastAPI()
db = SessionLocal()
player = Player()

@app.get("/channel/{channel_id}")
def stream_channel(channel_id: int):
    channel = db.query(Channels).get(channel_id)
    if not channel:
        return Response(status_code=404, content="Channel not found")

    runtime = ChannelRuntime(channel)

    def streamer():
        while True:
            schedule = runtime.get_active_schedule()
            if not schedule:
                continue

            playlist = db.query(Playlist).get(schedule.playlist_id)
            episodes = runtime.resolve_playlist_episodes(playlist)
            if not episodes:
                continue

            channel_offset = (datetime.now().astimezone() - channel.created_at).total_seconds()
            slot, internal_offset = runtime.resolve_episode_by_time(episodes, channel_offset)
            if not slot or internal_offset is None:
                continue

            ep = slot["episode"]
            segments = slot["segments"]

            yield from player.stream_segments(ep.file, segments, internal_offset)

    return StreamingResponse(streamer(), media_type="video/MP2T")


@app.get("/playlist.m3u")
def playlist_m3u():
    """
    Gera M3U dinâmico com todos os canais do banco.
    Cada canal aponta para /channel/{id}
    """
    channels = db.query(Channels).all()
    lines = ["#EXTM3U"]
    for ch in channels:
        lines.append(f'#EXTINF:-1,{ch.name}')
        lines.append(f'http://localhost:8000/channel/{ch.id}')
    content = "\n".join(lines)
    return Response(content, media_type="application/x-mpegURL")
