from . import config
import re
import os
import random
from moviepy.editor import *
from datetime import datetime, timedelta
from .Models import Catalog_Schedule, Catalog_List, Playlist_Files
from multiprocessing.pool import ThreadPool
from .Program import get_program, get_files_catalog, get_file
from .Edit_Video import cutout, include_video_personality


def include_schedule_playlist(programer: Catalog_Schedule):

    if programer.recurrent != None:
        date = datetime.now().date()+timedelta(days=-4)
        if programer.recurrent > date.weekday():
            days = programer.recurrent-date.weekday()
        elif programer.recurrent < date.weekday():
            days = (7-date.weekday())+programer.recurrent
        else:
            days = 0
        date = date+timedelta(days=days)
    elif programer.date != None:
        date = programer.date
    else:
        date = datetime.now().date()

    datetime_program = datetime.combine(date, programer.time)

    duration = programer.duration.total_seconds()

    include_files_catalog(programer.catalog_id, duration, datetime_program)


def include_files_catalog(programer: Catalog_List, duration: float, datetime: datetime):

    files = get_files_catalog(programer.id, programer.random)
    duration_programmer = duration
    for key, file in enumerate(files):
        video_duration = render_video(file['id'], datetime, duration_programmer == duration, key+1 == len(files))
        duration_programmer = duration_programmer-video_duration        
        if duration_programmer <= 0:
            video_duration = render_video(file['id'], datetime, duration_programmer == duration, True)
            break
        else:
            datetime = datetime+timedelta(seconds=video_duration)


def render_video(file_id: int, date_program: datetime, is_start_file: bool = False, is_end_file: bool = False, sequence_count: int = None, duration: float = 0):
    file = get_file(file_id)
    if file != None and os.path.exists(file.path):
        base_file = os.path.basename(file.path)
        print("Import File:", base_file)
        
        base_file = base_file_temp(base_file)
        cutoffs = file.cutoffs
        video = VideoFileClip(file.path)

        if 'opening' in cutoffs.keys():
            (start, end) = get_seconds_start_end(cutoffs['opening'])
            if is_start_file == False:
                # Remover Abertura caso tenha
                video = cutout(video, start, end)
            elif file.catalog_id.path_personality_opening != None and is_start_file == True:
                video = include_video_personality(
                    video, file.catalog_id.path_personality_opening, start, end)

        if 'completion' in cutoffs.keys() and is_end_file == False:
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

        # Delete Old File Has Existe
        delete_file_playlist(file.id, date_program)

        # Insert In Playlist
        Playlist_Files.insert({'catalog_id': file.catalog_id, 'file_id': file.id, 'file': base_file,
                               "date_start": date_program, "duration": str(timedelta(seconds=video_duration))}).execute()

        if file.sequence_id != None and is_end_file == False:
            if sequence_count != None:
                sequence_count = sequence_count-1
            date_program = date_program+timedelta(seconds=video_duration)

            if sequence_count == None or sequence_count > 0:
                return render_video(file.sequence_id, date_program, sequence_count=sequence_count, duration=video_duration)
        return video.duration+duration


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


def delete_file_playlist(file_id: int = None, date_programer: datetime = None):
    file_playlist = Playlist_Files.select(
        Playlist_Files.id, Playlist_Files.file_id, Playlist_Files.file, Playlist_Files.date_start)

    if file_id != None:
        file_playlist = file_playlist.where(Playlist_Files.file_id == file_id)

    if date_programer != None:
        file_playlist = file_playlist.where(
            Playlist_Files.date_start == date_programer)

    file_playlist = file_playlist.first()

    if file_playlist != None:
        os.remove("{}/{}".format(config.TEMP_PATH, file_playlist.file))
        Playlist_Files.delete_by_id(file_playlist.id)


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

    for programer in get_program(['14-09-2024'], ['17:00:00', '19:59:59']):
        include_schedule_playlist(programer)
