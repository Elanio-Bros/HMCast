import threading as thread
import time
import src.include_files as include_files
import src.load_stream as load_stream

def files():
    print("Files")
    while True:
        include_files.main()
        time.sleep(10)

def stream():
    print("Stream")
    while True:
        load_stream.main()

thread.Thread(target=stream).start()
thread.Thread(target=files).start()