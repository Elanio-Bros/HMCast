import threading as thread
import time
import src.include_files as include_files
import src.load_stream as load_stream
import src.render_file as render_files


def files():
    print("Files")
    while True:
        include_files.main()
        time.sleep(10)


def stream():
    print("Stream")
    while True:
        load_stream.main()
    
def render():
    print("Render")
    while True:
        render_files.main()

thread.Thread(target=stream).start()
thread.Thread(target=files).start()
thread.Thread(target=render).start()