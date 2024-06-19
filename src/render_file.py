from . import config
import os
from datetime import datetime, timedelta
from .Models import Playlist_Files
from peewee import fn
from vidgear.gears import StreamGear
import threading as thread
from multiprocessing.pool import ThreadPool


def render_video(id, value):
    file = value['file']
    time_start = value['time_start']
    stream_params = {
        "-video_source": file,
        "-streams": [
            # Stream1: 1920x1080
            {"-resolution": "1920x1080", "-video_bitrate": "2000k"},
            # # Stream2: 1280x720
            # {"-resolution": "1280x720",  "-video_bitrate": "1500k"},
            # # Stream3: 640x360
            # {"-resolution": "640x360", "-video_bitrate": "1000k"},
            # # Stream3: 320x240
            # {"-resolution": "320x240", "-video_bitrate": "500k"},

        ],
        "-hls_time": 5,
        "-clear_prev_assets": True
    }

    out = "{}/{}".format(config.RENDER_PATH, os.path.basename(file))
    if not os.path.exists(out):
        os.mkdir(out)

    streamer = StreamGear(output="{}/hls.m3u8".format(out),
                          format="hls", **stream_params)
    streamer.transcode_source()
    streamer.terminate()

    if datetime.now().time() > time_start:
        time_start = datetime.now()+timedelta(minutes=1)

    Playlist_Files.update({"file": os.path.basename(out), "render": True, 'time_start': time_start}).where(Playlist_Files.id == id).execute()
    os.remove(file)


def main():
    playlist = enumerate(Playlist_Files.select().where(Playlist_Files.render == 0).dicts(
    ).order_by(Playlist_Files.time_start.asc()).dicts())
    pool = ThreadPool(processes=2)
    for id, file in playlist:
        pool.apply_async(render_video,[file['id'], file])
    pool.close()
    pool.join()
