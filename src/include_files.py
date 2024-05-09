from . import config
import os
import ffmpeg_streaming
from ffmpeg_streaming import Formats, Bitrate, Representation, Size
from moviepy.editor import *
import sys
from datetime import datetime, timedelta
import time
from Models import Catalog_Day_Week, Catalog_Files, Playlist_Files
from peewee import fn

def code_videos(id, value, time_start, time_end, day_week_start, day_week_end):

    base_file = os.path.basename(value['path'])

    clip = VideoFileClip(value['path'])

    print("Import File:", base_file)

    if id >= 1 and value['time_after_opening'].strftime("%H:%M:%S") != "00:00:00":
        open = value['time_after_opening']
        seconds = open.hour*3600+open.minute*60+open.second
        # Remover Abertura caso tenha
        clip = clip.subclip(seconds, -1)

    origial_time_start = time_start
    time_start = (time_start + timedelta(seconds=clip.duration))
    valid_start_date = time_start.weekday(
    ) == day_week_end and time_start.time() >= time_end

    if valid_start_date == True and value['time_before_completion'].strftime("%H:%M:%S") != "00:00:00":
        final = value['time_before_completion']
        open = value['time_after_opening']
        seconds_start = open.hour*3600+open.minute*60+open.second
        seconds_final = (final.hour*3600)+(final.minute*60)+final.second

        # Remover Finalização caso tenha
        if seconds_final >= clip.duration:
            seconds_final = (seconds_final-seconds_start)

        clip = clip.subclip(0, seconds_final)

    clip=clip.subclip(0,20)

    if not os.path.exists("{}/{}/".format(config.TEMP_PATH, base_file)):
        def monitor(ffmpeg, duration, time_, time_left, process):
            per = round(time_ / duration * 100)
            sys.stdout.write(
                "\rTranscoding...(%s%%) %s left [%s%s]" %
                (per, timedelta(seconds=int(time_left)), '#' * per, '-' * (100 - per))
            )
            sys.stdout.flush()
    
        file = "{}/temp{}.mp4".format(config.TEMP_PATH, id)
        clip.write_videofile(file)
        clip.close()

        video = ffmpeg_streaming.input(file)
        _480p = Representation(Size(854, 480), Bitrate(750 * 1024, 192 * 1024))
        _720p = Representation(
            Size(1280, 720), Bitrate(2048 * 1024, 320 * 1024))
        _1080p = Representation(
            Size(1920, 1080), Bitrate(4096 * 1024, 320 * 1024))

        hls = video.hls(Formats.h264(), hls_time=5)
        hls.representations(_480p, _720p, _1080p)
        hls.flags('independent_segments')
        hls.output("{}/{}/hls.m3u8".format(config.TEMP_PATH,
                   base_file), monitor=monitor)
        os.remove(file)
    else:
        clip.close()

    Playlist_Files.insert(
        {"file_id": value['id'], "file": base_file, "duration": str(timedelta(seconds=clip.duration)), "time_start": origial_time_start.time(), "catalog_id": value['catalog_id'], "day_week": time_start.weekday()}).execute()

    if valid_start_date == True:
        time_start = False
    elif valid_start_date == False and value['sequence_id'] != None:
        file = Catalog_Files.select().where(Catalog_Files.watched == 0).where(
            Catalog_Files.id == value['sequence_id']).dicts()
        if (len(file) == 1):
            code_videos(id+1, file[0], time_start, time_end)

    return time_start


def main():
    # +timedelta(hours=7)
    date = datetime.now()
    date_start = date
    day_week_start = date_start.weekday()
    start_time = date_start.strftime("%H:{}:{}").format("00", "00")

    # pegando de 2 para frente
    date_end = date_start+timedelta(hours=1)
    day_week_end = date_end.weekday()
    end_time = date_end.strftime("%H:{}:{}").format(59, 59)

    catalog_now = Catalog_Day_Week.select().where(Catalog_Day_Week.day_week_start == day_week_start).where(Catalog_Day_Week.time_start >= start_time).where(
        Catalog_Day_Week.day_week_end == day_week_end).where(Catalog_Day_Week.time_end <= end_time).order_by(Catalog_Day_Week.time_start.asc())

    for value in catalog_now:
        files = Catalog_Files.select().where(Catalog_Files.watched == 0).where(
            Catalog_Files.catalog_id == value.catalog_id).order_by(Catalog_Files.id.asc()).dicts()
        if len(files) == 0:
            Catalog_Files.update({Catalog_Files.watched: 0}).where(
                Catalog_Files.catalog_id == value.catalog_id).execute()
        files = enumerate(Catalog_Files.select().where(Catalog_Files.watched == 0).where(
            Catalog_Files.catalog_id == value.catalog_id).order_by(Catalog_Files.id.asc() if value.catalog_id.random == False else fn.Random()).dicts())
        time_start = datetime.combine(date_start, value.time_start)
        file_has_list = Playlist_Files.select().where((Playlist_Files.catalog_id == value.catalog_id) & (
            (Playlist_Files.time_start.between(value.time_start, value.time_end)) & (Playlist_Files.day_week.between(value.day_week_start, value.day_week_end)))).dicts()
        if (len(file_has_list) == 0):
            for id, file in files:
                time_start = code_videos(
                    id, file, time_start, value.time_end, value.day_week_start, value.day_week_end)
                if time_start == False:
                    break


if __name__ == "__main__":
    main()
