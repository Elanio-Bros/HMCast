from . import config
from peewee import *
from playhouse.shortcuts import ThreadSafeDatabaseMetadata
from playhouse.sqliteq import SqliteQueueDatabase
from datetime import datetime
import json

__database__ = "{}/{}".format(config.DATABASE_PATH,config.DB_FILE)
db = SqliteQueueDatabase(__database__, pragmas={"foreign_keys": 1, "journal_mode": "WAL"})

class TimeData(Field):
    field_type = 'json'
    
    def db_value(self, value):
        return value
    
    def python_value(self, value):
        value=json.loads(value)
        def format(value):
            if '.' in value:
                return '%H:%M:%S.%f'
            else:
                return '%H:%M:%S'
        for val in value:
            value[val]['time-start']=datetime.strptime(value[val]['time-start'], format(value[val]['time-start'])).time()
            value[val]['time-end']=datetime.strptime(value[val]['time-end'], format(value[val]['time-end'])).time()
        return value
    
class Catalog_List(Model):
    id = IntegerField(primary_key=True)
    name = TextField()
    random = BooleanField(null=True, default="0")
    path_personality_opening = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata


class Catalog_Day_Week(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    # 0 Monday and 6 Sunday
    day_week_start = IntegerField(
        constraints=[Check('day_week_start <= 6'), Check('day_week_start >= 0')])
    time_start = TimeField(constraints=[Check(
        'time_start <= "23:59:59"'), Check('time_start >= "00:00:00"')])
    day_week_end = IntegerField(
        constraints=[Check('day_week_end <= 6'), Check('day_week_end >= 0')])
    time_end = TimeField(constraints=[Check('time_end <= "23:59:59"'), Check(
        'time_end >= "00:00:00"')])

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata


class Catalog_Files(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    watched = BooleanField(default=False)
    sequence_id = ForeignKeyField(
        'self', field="id", backref="sequence", null=True)
    path = TextField()
    cutoffs= TimeData(null=True,default="[]")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata


class Playlist_Files(Model):
    id = IntegerField(primary_key=True)
    catalog_id = ForeignKeyField(Catalog_List, field="id", backref="catalog")
    file_id = ForeignKeyField(Catalog_Files, field="id", backref="file")
    file = TextField()
    day_week = IntegerField(
        constraints=[Check('day_week <= 6'), Check('day_week >= 0')])
    time_start = TimeField(constraints=[Check(
        'time_start <= "23:59:59"'), Check('time_start >= "00:00:00"')])
    duration = TimeField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata
