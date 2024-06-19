import os
from . import config
import shutil
from .stream_media import Stream_Media
from .Models import Playlist_Files, Catalog_Files
from datetime import datetime, timedelta


def main():
    file_id = None

    # Tempo de agora
    date = datetime.now()
    day_week = date.weekday()
    time_start = date.strftime("%H:%M:%S")

    # list reproduction
    playlist = Playlist_Files.select().where(Playlist_Files.day_week == day_week).where(Playlist_Files.render == 1).dicts().where(
        Playlist_Files.time_start >= time_start).order_by(Playlist_Files.time_start.asc()).dicts()
    for midia in playlist:
        if (midia['file_id'] == file_id or datetime.now().strftime("%H:%M") == midia['time_start'].strftime("%H:%M")):
            dir = '{}/{}'.format(config.RENDER_PATH, midia['file'])
            if os.path.isdir(dir) and os.path.exists(dir):
                print("Execute File:{}".format(midia['file']))
                stream_resolution = []
                for resolution in range(0, 1):
                    stream_medias = Stream_Media(
                        resolution, config.DEFAULT_PATH, dir)
                    stream_resolution.append(stream_medias)
                for resolution in stream_resolution:
                    resolution.start()
                for resolution in stream_resolution:
                    resolution.join()

                # Removendo para limpeza
                # Thread
                Playlist_Files.delete_by_id(midia['id'])
                Catalog_Files.update({"watched": 1}).where(
                    Catalog_Files.id == midia['file_id']).execute()
                shutil.rmtree(dir+"/")
            file_id = midia['file_id']


if __name__ == "__main__":
    main()
