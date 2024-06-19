import os
from dotenv import load_dotenv

load_dotenv()
DEFAULT_PATH = os.getenv("DEFAULT_PATH")
TEMP_PATH = os.getenv("TEMP_PATH")
RENDER_PATH = os.getenv("RENDER_PATH")
DATABASE_PATH = os.getenv("DATABASE_PATH")
DB_FILE=os.getenv("DB_FILE")