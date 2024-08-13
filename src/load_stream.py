import os
from . import config
import shutil
from .Models import Playlist_Files, Catalog_Files
from datetime import datetime, timedelta
from vidgear.gears import StreamGear


def main():
    catalog_id = None

    # Tempo de agora
    date = datetime.now()
    day_week = date.weekday()
    time_start = date.strftime("%H:%M:%S")

    playlist = Playlist_Files.select().where(Playlist_Files.day_week == day_week).where(
        Playlist_Files.time_start >= time_start).order_by(Playlist_Files.time_start.asc()).dicts()
    for midia in playlist:
        if (midia['catalog_id'] == catalog_id or datetime.now().strftime("%H:%M") == midia['time_start'].strftime("%H:%M")):
            dir = '{}/{}'.format(config.RENDER_PATH, midia['file'])
            if os.path.isdir(dir) and os.path.exists(dir):
                stream_params = {
                    "-video_source": dir,
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
                    "-livestream": True,
                    "-hls_time": 5,
                    "-hls_list_size": 10,
                    "-hls_flags": "delete_segments+append_list+omit_endlist",

                }

            streamer = StreamGear(output="{}/hls.m3u8".format(config.DEFAULT_PATH),
                                  format="hls", custom_ffmpeg=config.IMAGEIO_FFMPEG_EXE, **stream_params)
            streamer.transcode_source()
            streamer.terminate()

            # # Removendo para limpeza
            # Playlist_Files.delete_by_id(midia['id'])
            # Catalog_Files.update({"watched": 1}).where(
            #     Catalog_Files.id == midia['file_id']).execute()
            # shutil.rmtree(dir+"/")
            # catalog_id = midia['catalog_id']


# def __removing_unused_files(self):
    # segments = [segment.uri for segment in original.segments]
    # for file in os.listdir():
    #     local_file = "{}/{}".format(self.default_path, file)
    #     if os.path.isfile(local_file) and os.path.splitext(file)[1] == '.ts' and "chunk-stream{}-".format(self.resolution) in file and file not in segments:
    #         os.remove(local_file)
