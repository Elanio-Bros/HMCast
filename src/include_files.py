from . import config
import os
from moviepy.editor import *
from datetime import datetime, timedelta
from .Models import Catalog_Day_Week, Catalog_Files, Playlist_Files
from peewee import fn
from multiprocessing.pool import ThreadPool


def code_videos(id, value, time_start, time_end, day_week_start, day_week_end, personality_opening=None):

    base_file = os.path.basename(value['path'])

    video = VideoFileClip(value['path'])
    print("Import File:", base_file)
    # Ajustar para poder cortar os videos na parte que quer

    def cutout(video, start, end):
        if (end >= video.duration):
            end = video.duration
        return concatenate_videoclips([video.subclip(0, start), video.subclip(end, video.duration)], method='compose')

    cutoffs = value['cutoffs']
    if 'opening' in cutoffs.keys():
        if personality_opening != None or id > 0:
            # Remover Abertura caso tenha
            (start, end) = get_seconds_start_end(cutoffs['opening'])
            clip = cutout(video, start, end)
        elif personality_opening != None and id == 0:
            clip1 = clip.subclip(0, start)
            opening = VideoFileClip(personality_opening)
            clip2 = clip.subclip(end-(end-start), clip.duration)
            clip = concatenate_videoclips(
                [clip1, opening, clip2], method='compose')
        else:
            clip = video
    origial_time_start = time_start
    time_start = (time_start + timedelta(seconds=clip.duration))
    valid_start_date = time_start.weekday(
    ) == day_week_end and time_start.time() >= time_end

    if valid_start_date == False and 'completion' in cutoffs.keys():
        # Remover Finalização caso tenha
        (start, end) = get_seconds_start_end(cutoffs['completion'])
        if start > clip.duration:
            (open_start, open_end) = get_seconds_start_end(cutoffs['opening'])
            start = start-open_end
            end = end-open_end
        clip = cutout(clip, start, end)

    file = "{}/{}_{}.mp4".format(config.TEMP_PATH, base_file, id)
    
    clip.write_videofile(file)

    date = get_date_time()['date']

    if date.time() > origial_time_start.time():
        origial_time_start = datetime.now()+timedelta(minutes=1)

    Playlist_Files.insert({"file_id": value['id'], "file": file, "render": False, "duration": str(timedelta(seconds=clip.duration)), "time_start":  origial_time_start.time(), "catalog_id": value['catalog_id'], "day_week": time_start.weekday()}).execute()
    
    video.close()
    
    if valid_start_date == True:
        time_start = False
    elif valid_start_date == False and value['sequence_id'] != None:
        file = Catalog_Files.select().where(Catalog_Files.watched == 0).where(
            Catalog_Files.id == value['sequence_id']).dicts()
        if (len(file) == 1):
            return code_videos(id+1, file[0], time_start, time_end, day_week_start, day_week_end, personality_opening)

    return time_start


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
    date_start = date
    date_end = date_start+timedelta(hours=1)

    return {"date": date, "date_start": date_start, "date_end": date_end}


def main():
    date = get_date_time()

    date_start = date["date_start"]
    day_week_start = date_start.weekday()
    start_time = date_start.strftime("%H:{}:{}").format("00", "00")

    date_end = date["date_end"]
    day_week_end = date_end.weekday()
    end_time = date_end.strftime("%H:{}:{}").format(59, 59)

    catalog_now = Catalog_Day_Week.select().where(
        Catalog_Day_Week.day_week_start == day_week_start).where(Catalog_Day_Week.time_start >= start_time).where(Catalog_Day_Week.day_week_end == day_week_end).where(Catalog_Day_Week.time_end <= end_time).order_by(Catalog_Day_Week.time_start.asc())
    for value in catalog_now:

        files = Catalog_Files.select().where(Catalog_Files.watched == 0).where(
            Catalog_Files.catalog_id == value.catalog_id).order_by(Catalog_Files.id.asc()).dicts()

        if len(files) == 0:
            Catalog_Files.update({Catalog_Files.watched: 0}).where(
                Catalog_Files.catalog_id == value.catalog_id).execute()

        files = enumerate(Catalog_Files.select().where(Catalog_Files.watched == 0).where(
            Catalog_Files.catalog_id == value.catalog_id).order_by(Catalog_Files.id.asc() if value.catalog_id.random == False else fn.Random()).dicts())

        file_has_list = Playlist_Files.select().where((Playlist_Files.catalog_id == value.catalog_id) & (
            (Playlist_Files.time_start.between(value.time_start, value.time_end)) & (Playlist_Files.day_week.between(value.day_week_start, value.day_week_end)))).dicts()

        if (len(file_has_list) == 0):
            time_start = datetime.combine(date_start, value.time_start)
            for id, file in files:
                time_start = code_videos(id, file, time_start, value.time_end, value.day_week_start,value.day_week_end, value.catalog_id.path_personality_opening)
                if time_start == False:
                    break

if __name__ == "__main__":
    main()
