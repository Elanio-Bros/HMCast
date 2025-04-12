import os
from dotenv import load_dotenv

load_dotenv()
DEFAULT_PATH = os.getenv("DEFAULT_PATH")
TEMP_PATH = os.getenv("TEMP_PATH")

DATABASE = os.getenv("DATABASE")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = int(os.getenv("DATABASE_PORT"))
DATABASE_USER=os.getenv("DATABASE_USER")
DATABASE_PASS=os.getenv("DATABASE_PASS")

IMAGEIO_FFMPEG_EXE=os.getenv("IMAGEIO_FFMPEG_EXE")
