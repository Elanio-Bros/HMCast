from datetime import datetime, time, date
from .Models import Catalog_Schedule, Catalog_Files
from peewee import fn


def get_program(date: date | list = None, time_start: time | list = None, day_week: int | list = None):
    programer = Catalog_Schedule.select(Catalog_Schedule.id, Catalog_Schedule.catalog_id,
                                        Catalog_Schedule.recurrent, Catalog_Schedule.date, Catalog_Schedule.time, Catalog_Schedule.duration)

    if date != None:
        if type(date) != list or (type(date) == list and len(date) == 1):
            date = date[0] if type(date) == list else date
            if type(date) == datetime:
                date = date.date()
            elif type(date) == str:
                date = datetime.strptime(date, "%Y-%m-%d").date()

            programer = programer.where((Catalog_Schedule.date == date) | (
                Catalog_Schedule.recurrent == date.weekday()))
        elif type(date) == list:
            date = [datetime.strptime(date, "%Y-%m-%d").date()
                    for date in date]
            if len(date) == 2:
                week = [date.weekday() for date in date]
                week.sort()
                programer = programer.where((Catalog_Schedule.date.between(date[0],  date[1])) | (
                    Catalog_Schedule.recurrent.between(week[0], week[1])))
            elif len(date) > 2:
                raise Warning(
                    "argument date exceeded the limit of 2 arguments in the list")

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

    return programer.order_by(Catalog_Schedule.time.asc(), Catalog_Schedule.recurrent.asc(), Catalog_Schedule.date.asc())


def get_files_catalog(catalog_id: int, random: bool):

    files = Catalog_Files.select(Catalog_Files.id, Catalog_Files.path).where(
        Catalog_Files.watched == 0).where(Catalog_Files.catalog_id == catalog_id).order_by(Catalog_Files.id.asc() if random == False else fn.Random())

    if len(files) == 0:
        Catalog_Files.update({Catalog_Files.watched: 0}).where(
            Catalog_Files.catalog_id == catalog_id).execute()
        return get_files_catalog(catalog_id, random)
    else:
        return files.dicts()


def get_file(file_id: int):
    files = Catalog_Files.select(Catalog_Files.id, Catalog_Files.catalog_id, Catalog_Files.sequence_id, Catalog_Files.path, Catalog_Files.cutoffs).where(
        Catalog_Files.watched == 0).where(Catalog_Files.id == file_id)
    return files.first()
