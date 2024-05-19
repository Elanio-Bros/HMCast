import os
import config
import shutil
from playhouse.sqliteq import SqliteQueueDatabase
from Models import Catalog_List,Catalog_Day_Week,Catalog_Files,Playlist_Files

# Create Path Temp
if not os.path.exists('{}/'.format(config.TEMP_PATH)):
    os.mkdir('{}/'.format(config.TEMP_PATH))

# create past if is not exists
if not os.path.exists('{}/'.format(config.DEFAULT_PATH)):
    os.mkdir('{}/'.format(config.DEFAULT_PATH))
else:
    # clear past files
    shutil.rmtree('{}/'.format(config.DEFAULT_PATH), True)
    
__database__ = "{}/{}".format(config.DATABASE_PATH,config.DB_FILE)
db = SqliteQueueDatabase(__database__, pragmas={"foreign_keys": 1, "journal_mode": "WAL"})
# Create Database
db.create_tables([Catalog_List,Catalog_Day_Week,Catalog_Files,Playlist_Files])
db.stop()
    
