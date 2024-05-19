import os
import config
import shutil
from stream_media import Stream_Media
from Models import Playlist_Files, Catalog_Files
from datetime import datetime, timedelta
import time


def main():
    uri = None
    path = None

    # Tempo de agora
    date = datetime.now()
    day_week = date.weekday()
    # time_start = date.strftime("%H:%M:%S")

    # list reproduction
    playlist = Playlist_Files.select().where(Playlist_Files.day_week == day_week).dicts()
    # .where(Playlist_Files.time_start >= time_start).order_by(Playlist_Files.time_start.asc()).dicts()
    for midia in playlist:
        # if (date.strftime("%H:%M:%S") == midia['time_start'].strftime("%H:%M:%S")):
            dir = '{}/{}'.format(config.TEMP_PATH, midia['file'])
            if os.path.isdir(dir) and os.path.exists(dir):
                print("Execute File:{}".format(midia['file']))
                stream_resolution = []
                for resolution in range(0, 4):
                    stream_medias = Stream_Media(resolution, config.DEFAULT_PATH, dir, uri, path)
                    stream_resolution.append(stream_medias)
                for resolution in stream_resolution:
                    resolution.start()
                for resolution in stream_resolution:
                    resolution.join()

                    # Removendo para limpeza
                Playlist_Files.delete_by_id(midia['id'])
                playlist_values = [value['file_id']
                                   for value in Playlist_Files.select().dicts()]
                if os.path.isdir(dir) and os.path.exists(dir) and not midia['file_id'] in playlist_values:
                    Catalog_Files.update({"watched": 1}).where(
                        Catalog_Files.id == midia['file_id']).execute()
                    shutil.rmtree(dir+"/")


if __name__ == "__main__":
    main()
