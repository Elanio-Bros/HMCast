import threading as thread
import time
import src.include_files as include_files
import src.load_stream as load_stream
from datetime import datetime, timedelta

thread.Thread(target=load_stream.main).start()
thread.Thread(target=include_files.files_minute).start()