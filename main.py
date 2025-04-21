import threading as thread
from src.include_files import files_minute
import src.load_stream as load_stream
from src.load_stream import get_playlist
import time
import schedule

def run_threaded(job_func):
    job_thread = thread.Thread(target=job_func)
    job_thread.start()

def cron():
    print("Start Cron...")
    schedule.every(1).minutes.do(run_threaded,files_minute)
    schedule.every(1).seconds.do(run_threaded,get_playlist)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            break


run_threaded(cron)
run_threaded(load_stream.run_playlist)
