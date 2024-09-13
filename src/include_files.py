from . import config
import re
import os
from moviepy.editor import *
from datetime import datetime, timedelta
from .Models import Catalog_Schedule, Catalog_Files, Playlist_Files
from multiprocessing.pool import ThreadPool
from .Program import get_program, get_files_catalog, get_file
from .Edit_Video import cutout, include_video_personality


def include_files_playlist(programer: Catalog_Schedule):

    if programer.recurrent != None:
        date = datetime.now().date()
        if programer.recurrent > date.weekday():
            days = programer.recurrent-(date.weekday() % 6)
        elif programer.recurrent < date.weekday():
            days = (date.weekday() % 6)+programer.recurrent+1
        else:
            days = 0
        date = date+timedelta(days=days)
    elif programer.date != None:
        date = programer.date
    else:
        date = datetime.now().date()

    datetime_program = datetime.combine(date, programer.time)
    duration = programer.duration.total_seconds()

    files = get_files_catalog(programer.catalog_id,
                              programer.catalog_id.random)
    for file in files:
        render = render_video_duration(file['id'], duration, datetime_program,
                              duration == programer.duration.total_seconds())
        duration = render['duration']
        datetime_program = render['date']
        if duration <= 0:
            break


def render_video_duration(file_id: int, duration: float, date_program: datetime, is_start_file: bool = False):
    file = get_file(file_id)
    if os.path.exists(file.path):

        base_file = os.path.basename(file.path)
        base_file = base_file_temp(base_file)
        cutoffs = file.cutoffs
        print("Import File:", base_file)
        video = VideoFileClip(file.path)

        if 'opening' in cutoffs.keys():
            (start, end) = get_seconds_start_end(cutoffs['opening'])
            if is_start_file == False:
                # Remover Abertura caso tenha
                video = cutout(video, start, end)
            elif file.catalog_id.path_personality_opening != None:
                video = include_video_personality(
                    video, file.catalog_id.path_personality_opening, start, end)

        if 'completion' in cutoffs.keys() and duration > 0:
            # Remover Finalização caso tenha
            (start, end) = get_seconds_start_end(cutoffs['completion'])
            if start > video.duration and 'opening' in cutoffs.keys():
                (open_start, open_end) = get_seconds_start_end(
                    cutoffs['opening'])
                start = start-open_end
                end = end-open_end
            video = cutout(video, start, end)

        video_duration = video.duration

        video.write_videofile(
            "{}/{}".format(config.TEMP_PATH, base_file), threads=2)
        video.close()

        # Insert In Playlist
        Playlist_Files.insert({'catalog_id': file.catalog_id, 'file_id': file.id, 'file': base_file,
                              "date_start": date_program, "duration": str(timedelta(seconds=video_duration))}).execute()

        duration = duration-video_duration
        date_program = date_program+timedelta(seconds=video_duration)
        if file.sequence_id != None and duration > 0:
            # is_start_file é sempre falso pq ele nunca vai ser o primeiro arquivo
            return render_video_duration(file.sequence_id, duration, date_program)

    return {'duration': duration, 'date': date_program}


def base_file_temp(base_file: str, file_id: int = 0):
    file_id = file_id+1
    if os.path.exists("{}/{}".format(config.TEMP_PATH, base_file)):
        if re.search("\d+\_", base_file):
            base_file = re.sub("\d+\_", "{}_".format(file_id), base_file)
        else:
            base_file = "{}_{}".format(file_id, base_file)
        return base_file_temp(base_file, file_id)
    return base_file


def get_seconds_start_end(value):
    start = value['time-start']
    end = value['time-end']
    start = timedelta(hours=start.hour, minutes=start.minute,
                      seconds=start.second, microseconds=start.microsecond).total_seconds()
    end = timedelta(hours=end.hour, minutes=end.minute,
                    seconds=end.second, microseconds=end.microsecond).total_seconds()
    return start, end


def get_date_time():
    # +timedelta(hours=1)
    date = datetime.now()
    d_start = date
    d_end = d_start+timedelta(hours=1)

    return [date, d_start, d_end]


def main():
    # date, d_start, d_end = get_date_time()

    # day_start, start_time = d_start.weekday(), d_start.strftime("%H:{}:{}").format("00", "00")

    # day_end, end_time = d_end.weekday(), d_end.strftime("%H:{}:{}").format(59, 59)

    for programer in get_program(['12-09-2024'], ['17:00:00', '19:59:59']):
        include_files_playlist(programer)
