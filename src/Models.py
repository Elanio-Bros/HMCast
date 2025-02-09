from . import config
from peewee import *
from datetime import datetime, timedelta
import json

__database__ = "{}/{}".format(config.DATABASE_PATH, config.DB_FILE)
db = MySQLDatabase('video_tv', user='user_video_tv',
                   password='123456789', host='192.168.2.250', port=3306)


class TimeData(Field):
    field_type = 'json'

    def db_value(self, value):
        return value

    def python_value(self, value):
        value = json.loads(value)

        def format(value):
            if value != None:
                if '.' in value:
                    return '%H:%M:%S.%f'
                else:
                    return '%H:%M:%S'

        def is_zero(times):
            not_zero = True
            for name in times:
                time = times[name]
                second = timedelta(hours=time.hour, minutes=time.minute,
                                   seconds=time.second, microseconds=time.microsecond).total_seconds()
                if second > 0.0:
                    not_zero = False
            return not_zero

        if value != None:
            for val in value:
                value[val]['time-start'] = datetime.strptime(
                    value[val]['time-start'], format(value[val]['time-start'])).time()
                value[val]['time-end'] = datetime.strptime(
                    value[val]['time-end'], format(value[val]['time-end'])).time()
                if is_zero(value[val]) == True:
                    value[val] = None

            # Se todos os valores for 0 então retornar None se não retornar os que não são None
            if all(value[name] is None for name in value):
                return None
            else:
                return value


class TimeDelta(Field):
    field_type = 'time'

    def db_value(self, value):
        return value

    def python_value(self, value):
        return value


class Catalog_List(Model):
    id = IntegerField(primary_key=True)
    name = TextField()
    random = BooleanField(null=False, default="0")
    path_personality_opening = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class Catalog_Schedule(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    # 0 Monday and 6 Sunday
    recurrent = IntegerField(null=True, constraints=[Check(
        'recurrent <= 6 OR recurrent IS NULL'), Check('recurrent >= 0 OR recurrent IS NULL')])
    date = DateField(null=True)
    time = TimeField(
        constraints=[Check('time <= "23:59:59"'), Check('time >= "00:00:00"')])
    duration = TimeDelta()

    class Meta:
        database = db

        constraints = [
            Check("CASE WHEN recurrent IS NULL THEN date IS NOT NULL END = 1")]


class Catalog_Files(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    watched = BooleanField(default=False)
    sequence_id = ForeignKeyField(
        'self', field="id", backref="sequence", null=True)
    path = TextField()
    cutoffs = TimeData(null=True, default="[]")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class Playlist_Files(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    file_id = ForeignKeyField(Catalog_Files, field="id", backref="file")
    file = TextField()
    date_start = DateTimeField()
    duration = TimeField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db


def create_table():
    print("Create Tables")
    # Create Table
    db.create_tables([Catalog_List, Catalog_Schedule,
                     Catalog_Files, Playlist_Files])
