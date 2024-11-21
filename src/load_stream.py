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
    thread.Thread(target=get_playlist).start()
    thread.Thread(target=run_playlist).start()


def __ffmpge_io(video):
    ffmpeg.input(video).output("{}/stream.m3u8".format(config.DEFAULT_PATH), format='hls', **
                               {
        "threads": 1,
        "c:v": "libx264",
        "crf": 21,

        "c:a": "aac",
        "b:a": "128k",
        "ac": 2,
        "fflags":"nobuffer+flush_packets",
        "segment_list_type": "hls",
        "segment_list_flags": "+live",
        "hls_flags": "delete_segments+append_list+omit_endlist+split_by_time",
        "hls_delete_threshold": 14,
        "hls_list_size": 15,
        "hls_time": 5,
        "hls_segment_filename": "{}/{}".format(config.DEFAULT_PATH, "stream_%d.ts"),
    }).run(cmd=config.IMAGEIO_FFMPEG_EXE),


def __stream_unused_files(midia, dir):

    # Playlist_Files.delete_by_id(midia['id'])
    # Catalog_Files.update({"watched": 1}).where(
    #     Catalog_Files.id == midia['file_id']).execute()

    # if os.path.exists(dir):
    #     os.remove(dir)

    file_playlist = "{}/stream.m3u8".format(config.DEFAULT_PATH)
    if (os.path.exists(file_playlist)):
        playlist = m3u8.load(file_playlist)
        segments = [segment.uri for segment in playlist.segments]
        for file in os.listdir(config.DEFAULT_PATH):
            local_file = "{}/{}".format(config.DEFAULT_PATH, file)
            if os.path.isfile(local_file) and os.path.splitext(file)[1] == '.ts' and file not in segments:
                os.remove(local_file)


def get_playlist():
    global playlist
    date_now = None
    while True:
        # .now()
        date = datetime(2024, 11, 20, 10, 15, 00,
                        00).strftime('%Y-%m-%d %H:%M:%S')
        if date != date_now:
            playlist_files = Playlist_Files.select().where(Playlist_Files.date_start ** "{}{}".format(date, "%")).order_by(
                Playlist_Files.date_start.asc()).order_by(Playlist_Files.catalog_id.asc()).dicts()
            playlist = playlist + [*playlist_files]
            date_now = date


def run_playlist():
    global playlist
    play = []
    while True:
        play = play+playlist
        for midia in play:
            if len(playlist) >= 1:
                try:
                    dir = '{}/{}'.format(config.TEMP_PATH, midia['file'])
                    if os.path.exists(dir):
                        print("Process Midia:", dir)
                        __ffmpge_io(dir)
                except Exception as e:
                    print("Erro:", e)
                    print("Midia:", midia['file'])
                # Removendo para limpeza
                thread.Thread(target=__stream_unused_files,
                              args=[midia, dir]).start()
