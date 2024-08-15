import os
from src import config
import shutil
from src.Models import create_table

# Create Path Temp
if not os.path.exists('{}/'.format(config.TEMP_PATH)):
    os.mkdir('{}/'.format(config.TEMP_PATH))

if not os.path.exists('{}/'.format(config.DEFAULT_PATH)):
    os.mkdir('{}/'.format(config.DEFAULT_PATH))
else:
    # clear path files
    shutil.rmtree('{}/'.format(config.DEFAULT_PATH), True)
    os.mkdir('{}/'.format(config.DEFAULT_PATH))

# create_databases
create_table()
