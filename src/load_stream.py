import os
from . import config
import threading as thread
from .Models import Playlist_Files, Catalog_Files
from datetime import datetime
import ffmpeg
import m3u8
from multiprocessing.pool import ThreadPool

playlist = []


def main():
    print("Stream")
    # thread.Thread(target=get_playlist).start()
    thread.Thread(target=run_playlist).start()


def __ffmpge_io(video):
    ffmpeg.input(video).output("{}/stream.m3u8".format(config.DEFAULT_PATH), format='hls', **
                               {
        # filter:v:0 scale=w=480:h=360  -maxrate:v:0 600k -b:a:0 500k
        # "map": ["0:v:0", "0:a:0", "0:v:0", "0:a:0", "0:v:0", "0:a:0"],
        # "var_stream_map": "v:0,a:0,name:720p",
        # .filter("filter:v:0 scale=w=1280:h=720")
        "threads": "4",
        "c:v": "libx264",
        "hls_flags": "delete_segments+append_list+omit_endlist",
        "hls_list_size": 10,
        "hls_time": 5,
        "hls_segment_filename": "{}/{}".format(config.DEFAULT_PATH, "stream_%d.ts"),
        # "master_pl_name": "{}/stream.m3u8".format(config.DEFAULT_PATH)
    }).run(cmd=config.IMAGEIO_FFMPEG_EXE),

    # stream_params = {
    #     "-video_source": dir,
    #     "-streams": [
    #         # Stream1: 1920x1080
    #         {"-resolution": "1920x1080",
    #          "-video_bitrate": "2000k"},
    #         # # Stream2: 1280x720
    #         {"-resolution": "1280x720",
    #          "-video_bitrate": "1500k"},
    #         # # Stream3: 640x360
    #         # {"-resolution": "640x360", "-video_bitrate": "1000k"},
    #         # # Stream3: 320x240
    #         # {"-resolution": "320x240", "-video_bitrate": "500k"},

    #     ],
    #     "-livestream": True,
    #     "-hls_time": 5,
    #     "-hls_list_size": 10,
    #     "-hls_flags": "delete_segments+append_list+omit_endlist",
    # }

    # streamer = StreamGear(output="{}/hls.m3u8".format(config.DEFAULT_PATH),
    #                       format="hls", custom_ffmpeg=config.IMAGEIO_FFMPEG_EXE, **stream_params)
    # streamer.transcode_source()
    # streamer.terminate()


def __stream_unused_files(midia, dir, count_resolution):

    Playlist_Files.delete_by_id(midia['id'])
    Catalog_Files.update({"watched": 1}).where(
        Catalog_Files.id == midia['file_id']).execute()

    if os.path.exists(dir):
        os.remove(dir)

    pool = ThreadPool(processes=2)
    for resolution in range(0, count_resolution+1):
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


def get_playlist():
    global playlist
    date_now = None
    while True:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if date != date_now:
            playlist_files = Playlist_Files.select().where(Playlist_Files.date_start ** "{}{}".format(date, "%")).order_by(
                Playlist_Files.date_start.asc()).order_by(Playlist_Files.catalog_id.asc()).dicts()
            playlist = playlist + [*playlist_files]
            date_now = date


def run_playlist():
    global playlist
    play = []
    file = '{}/{}'.format(config.TEMP_PATH, 't1.mp4')
    __ffmpge_io(file)
    # while True:
    # play = play+playlist
    # for midia in play:
    #     if len(playlist) >= 1:
    #         dir = '{}/{}'.format(config.TEMP_PATH, midia['file'])
    #         if os.path.exists(dir):
    #             print("Process Midia:", midia['file'])
    #             # try:

    # except Exception as e:
    #     print("Erro:", e)
    #     print("Midia:", midia['file'])

    # # Removendo para limpeza
    # thread.Thread(target=__stream_unused_files, args=[
    #               midia, dir, len(stream_params['-streams'])]).start()
