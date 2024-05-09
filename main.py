import threading as thread
import time
import os
import shutil
import src.include_files as include_files
import src.load_stream as load_stream
import database.Models as models
import config


def files():
    print("Files")
    while True:
        include_files.main()
        time.sleep(10)


def stream():
    print("Stream")
    while True:
        load_stream.main()

# Create Path Temp
if not os.path.exists('{}/'.format(config.TEMP_PATH)):
    os.mkdir('{}/'.format(config.TEMP_PATH))

# create past if is not exists
if not os.path.exists('{}/'.format(config.DEFAULT_PATH)):
    os.mkdir('{}/'.format(config.DEFAULT_PATH))
else:
    # clear past files
    shutil.rmtree('{}/'.format(config.DEFAULT_PATH), True)

thread.Thread(target=files).start()
thread.Thread(target=stream).start()
input("Erro")
