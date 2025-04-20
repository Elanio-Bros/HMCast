import threading as thread
from src.include_files import files_minute
import src.load_stream as load_stream
from src.load_stream import get_playlist
import time
import schedule


def cron():
    print("Start Cron...")
    schedule.every(1).minutes.do(files_minute)
    schedule.every(1).seconds.do(get_playlist)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            break


thread.Thread(target=cron).start()
thread.Thread(target=load_stream.run_playlist).start()
