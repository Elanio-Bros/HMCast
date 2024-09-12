from . import config
from peewee import *
from playhouse.shortcuts import ThreadSafeDatabaseMetadata
from playhouse.sqliteq import SqliteQueueDatabase
from datetime import datetime, timedelta
import json

__database__ = "{}/{}".format(config.DATABASE_PATH, config.DB_FILE)
db = SqliteQueueDatabase(__database__, use_gevent=False, queue_max_size=64, pragmas={
                         "foreign_keys": 1, "journal_mode": "WAL"})

class TimeData(Field):
    field_type = 'json'

    def db_value(self, value):
        return value

    def python_value(self, value):
        value = json.loads(value)

        def format(value):
            if '.' in value:
                return '%H:%M:%S.%f'
            else:
                return '%H:%M:%S'
        for val in value:
            value[val]['time-start'] = datetime.strptime(
                value[val]['time-start'], format(value[val]['time-start'])).time()
            value[val]['time-end'] = datetime.strptime(
                value[val]['time-end'], format(value[val]['time-end'])).time()
        return value

class TimeDelta(Field):
    field_type='time'
    
    def db_value(self, value):
        return value
    def python_value(self, value):
        value= datetime.strptime(value, "%H:%M:%S").time() 
        value = timedelta(hours=value.hour,minutes=value.minute,seconds=value.second)
        return value
    

class Catalog_List(Model):
    id = IntegerField(primary_key=True)
    name = TextField()
    random = BooleanField(null=False, default="0")
    path_personality_opening = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata


class Catalog_Schedule(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    # 0 Monday and 6 Sunday
    recurrent = IntegerField(null=True, constraints=[Check('recurrent <= 6 OR recurrent IS NULL'), Check('recurrent >= 0 OR recurrent IS NULL')])
    date = DateField(null=True, constraints=[Check("CASE WHEN recurrent IS NULL THEN date IS NOT NULL END")])
    time = TimeField(constraints=[Check('time <= "23:59:59"'), Check('time >= "00:00:00"')])
    duration = TimeDelta()

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata


class Catalog_Files(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    watched = BooleanField(default=False)
    sequence_id = ForeignKeyField('self', field="id", backref="sequence", null=True)
    path = TextField()
    cutoffs = TimeData(null=True, default="[]")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata


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
        model_metadata_class = ThreadSafeDatabaseMetadata


def create_table():
    print("Create Tables")
    # Create Table
    db.create_tables([Catalog_List, Catalog_Schedule, Catalog_Files, Playlist_Files])
    db.stop()