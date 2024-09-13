import os
from . import config
import shutil
import threading as thread
from .Models import Playlist_Files, Catalog_Files
from datetime import datetime, timedelta
from vidgear.gears import StreamGear
import m3u8
from multiprocessing.pool import ThreadPool


def main():
    catalog_id = None

    # Tempo de agora
    # Pegar os do dia de hoje
    date = datetime.now()
    # day_week = date.weekday()
    # time_start = date.strftime("%H:%M:%S")
    
    # Refactoring for reload playlist
    playlist = Playlist_Files.select().where(Playlist_Files.date_start == date).order_by(Playlist_Files.time_start.asc()).dicts()

    for midia in playlist:
        # Thread
        if (midia['catalog_id'] == catalog_id or datetime.now().strftime("%H:%M") == midia['time_start'].strftime("%H:%M")):
            dir = '{}/{}'.format(config.TEMP_PATH, midia['file'])
            if os.path.exists(dir):
                stream_params = {
                    "-video_source": dir,
                    "-streams": [
                        # Stream1: 1920x1080
                        {"-resolution": "1920x1080",
                            "-video_bitrate": "2000k"},
                        # # Stream2: 1280x720
                        # {"-resolution": "1280x720",  "-video_bitrate": "1500k"},
                        # # Stream3: 640x360
                        # {"-resolution": "640x360", "-video_bitrate": "1000k"},
                        # # Stream3: 320x240
                        # {"-resolution": "320x240", "-video_bitrate": "500k"},

                    ],
                    "-livestream": True,
                    "-hls_time": 5,
                    "-hls_list_size": 10,
                    "-hls_flags": "delete_segments+append_list+omit_endlist",

                }

                streamer = StreamGear(output="{}/hls.m3u8".format(config.DEFAULT_PATH),
                                      format="hls", custom_ffmpeg=config.IMAGEIO_FFMPEG_EXE, **stream_params)
                streamer.transcode_source()
                streamer.terminate()

            # Removendo para limpeza
                thread.Thread(target=__stream_unused_files).start()
                Playlist_Files.delete_by_id(midia['id'])
                Catalog_Files.update({"watched": 1}).where(
                    Catalog_Files.id == midia['file_id']).execute()
                os.remove(dir)
                catalog_id = midia['catalog_id']


def __stream_unused_files():
    pool = ThreadPool(processes=2)
    for resolution in range(0, 2):
        pool.apply_async(__removing_files, [resolution])
    pool.close()
    pool.join()


def __removing_files(resolution):
    file_playlist = "{}/stream_{}.m3u8".format(config.DEFAULT_PATH, resolution)
    if (os.path.exists(file_playlist)):
        playlist = m3u8.load(file_playlist)
        segments = [segment.uri for segment in playlist.segments]
        for file in os.listdir(config.DEFAULT_PATH):
            local_file = "{}/{}".format(config.DEFAULT_PATH, file)
            if os.path.isfile(local_file) and os.path.splitext(file)[1] == '.ts' and "chunk-stream{}-".format(resolution) in file and file not in segments:
                os.remove(local_file)
