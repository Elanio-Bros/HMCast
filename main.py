import threading as thread
import src.include_files as include_files
import src.load_stream as load_stream

thread.Thread(target=load_stream.main).start()
thread.Thread(target=include_files.files_minute).start()