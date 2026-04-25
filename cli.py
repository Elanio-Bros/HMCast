import os
import sys
from dotenv import load_dotenv
from app.database import engine
from app.models import Base
from app.tui.app import VideoTVApp

load_dotenv()

if __name__ == "__main__":
    # Garante que o banco exista antes de subir a TUI
    Base.metadata.create_all(bind=engine)
    
    app = VideoTVApp()
    app.run()
