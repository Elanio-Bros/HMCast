from . import config
import os
from moviepy.editor import *
from datetime import datetime, timedelta, time, date
from .Models import Catalog_Schedule, Catalog_Files, Playlist_Files
from peewee import fn
from multiprocessing.pool import ThreadPool

def include_files_playlist(programer: Catalog_Schedule):
    
    duration=programer.duration.total_seconds()
    files=get_files_catalog(programer.catalog_id, programer.catalog_id.random)
    
    # for file in files:

        # if time.time() >= time_start.time() or time.weekday() != time_start.weekday():
        #   time_start = time+timedelta(minutes=1)

        # print(time_start.time().strftime("%H:%M:%S"),time_start.weekday())
        # bug fim list
        # Cacular Diferença das datas da programação e verificar se a soma de minutos é igual ou maior que a apresentada
        # valid_start_date = time_start.weekday() == programer.day_week_end and time_start.time() >= programer.time_end
        # # valid_start_date = time_start.weekday() == day_week_end and time_start.time() >= time_end
        # print(valid_start_date,time_start.weekday(), programer.day_week_end,time_start.time(),programer.time_end)
        # if valid_start_date==True:
        #     break


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


def get_program(date: date | list = None, time_start: time | list = None, day_week: int | list = None, ):
    programer = Catalog_Schedule.select(Catalog_Schedule.id, Catalog_Schedule.catalog_id,
                                        Catalog_Schedule.recurrent, Catalog_Schedule.date, Catalog_Schedule.time, Catalog_Schedule.duration)

    if date != None:
        if type(date) != list or (type(date) == list and len(date) == 1):
            date = date[0] if type(date) == list else date
            date = datetime.strptime(date, "%d-%m-%Y").date()
            programer = programer.where((Catalog_Schedule.date == date) | (Catalog_Schedule.recurrent==date.weekday()))
        elif type( date) == list:
            date = [datetime.strptime(date, "%d-%m-%Y").date() for date in  date]
            if len(date) == 2:
                programer = programer.where((Catalog_Schedule.date.between(date[0],  date[1])) | (Catalog_Schedule.recurrent.between(date[0].weekday(),  date[1].weekday())))
            elif len(date) > 2:
                raise Warning("argument date exceeded the limit of 2 arguments in the list")

    if day_week != None:
        if (type(day_week) == int or (type(day_week) == list and len(day_week) == 1)):
            day_week = day_week if type(day_week) == int else day_week[0]
            programer = programer.where(Catalog_Schedule.recurrent == day_week)
        elif type(day_week) == list and len(day_week) == 2:
            programer = programer.where(
                Catalog_Schedule.recurrent.between(day_week[0], day_week[1]))
        elif type(day_week) == list and len(day_week) > 2:
            programer = programer.where(Catalog_Schedule.recurrent << day_week)

    if time_start != None:
        if type(time_start) != list or (type(time_start) == list and len(time_start) == 1):
            time_start = time_start[0] if type(
                time_start) == list else time_start
            time_start = datetime.strptime(time_start, "%H:%M:%S").time()
            programer = programer.where(Catalog_Schedule.time == time_start)
        elif type(time_start) == list:
            time_start = [datetime.strptime(
                time, "%H:%M:%S").time() for time in time_start]
            if len(time_start) == 2:
                programer = programer.where(
                    Catalog_Schedule.time.between(time_start[0], time_start[1]))
            elif len(time_start) > 2:
                programer = programer.where(
                    Catalog_Schedule.time << time_start)

    return programer.order_by(Catalog_Schedule.time.asc())


def get_files_catalog(catalog_id, random):

    files = Catalog_Files.select(Catalog_Files.id, Catalog_Files.catalog_id, Catalog_Files.sequence_id, Catalog_Files.path, Catalog_Files.cutoffs).where(
        Catalog_Files.watched == 0).where(Catalog_Files.catalog_id == catalog_id).order_by(Catalog_Files.id.asc() if random == False else fn.Random())

    if len(files) == 0:
        Catalog_Files.update({Catalog_Files.watched: 0}).where(
            Catalog_Files.catalog_id == catalog_id).execute()
        return get_files_catalog(catalog_id)
    else:
        return enumerate(files.dicts())


def main():
    # date, d_start, d_end = get_date_time()

    # day_start, start_time = d_start.weekday(), d_start.strftime("%H:{}:{}").format("00", "00")

    # day_end, end_time = d_end.weekday(), d_end.strftime("%H:{}:{}").format(59, 59)

    for programer in get_program(['10-09-2024','11-09-2024'],['17:00:00','17:59:59']):
        include_files_playlist(programer)
