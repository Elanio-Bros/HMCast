from . import config
from peewee import *
from datetime import datetime, timedelta
import json

db = MySQLDatabase(config.DATABASE, user=config.DATABASE_USER,
                   password=config.DATABASE_PASS, host=config.DATABASE_HOST, port=config.DATABASE_PORT, field_types={'enum': 'enum'})


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

class EnumField(Field):
    field_type = 'enum'
    def __init__(self, choices, **kwargs):
        enum_values = ', '.join(f'"{val}"' for val in choices)
        self.field_type = f'ENUM({enum_values})'
        super().__init__(choices=choices,**kwargs)
        
    def db_value(self, value):
        if(type(value) != int):
            if value not in self.choices:
                raise ValueError(f"Value '{value}' invalid for ENUM: {self.choices}")

        return value
    
    def python_value(self, value):
        return (self.choices.index(value)+1,value)

class TimeDelta(Field):
    field_type = 'time'

    def db_value(self, value):
        return value

    def python_value(self, value):
        return value

class Catalog_List(Model):
    id = AutoField()
    name = TextField()
    random = BooleanField(null=False, default="0")
    path_personality_opening = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db

class Catalog_Schedule(Model):
    id = AutoField()
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    # 1 Monday and 7 Sunday
    recurrent = EnumField(choices=['monday','tuesday','wednesday','thursday','friday','saturday','sunday'])
    # IntegerField(null=True, constraints=[Check(
    # 'recurrent <= 6 OR recurrent IS NULL'), Check('recurrent >= 0 OR recurrent IS NULL')])
    date = DateField(null=True)
    time = TimeField(constraints=[Check('time <= "23:59:59"'), Check('time >= "00:00:00"')])
    duration = TimeDelta()

    class Meta:
        database = db

        constraints = [
            Check("CASE WHEN recurrent IS NULL THEN date IS NOT NULL END = 1")]

class Catalog_Files(Model):
    id = AutoField()
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
    id = AutoField()
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    file_id = ForeignKeyField(Catalog_Files, field="id", backref="file")
    type_video = EnumField(choices=['start','end'], null=True)
    file = TextField()
    date_start = DateTimeField()
    estimated_duration = TimeField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db


def create_table():
    print("Create Tables")
    # logging.basicConfig(level=logging.DEBUG)
    db.create_tables([Catalog_List, Catalog_Files,Catalog_Schedule, Playlist_Files])
