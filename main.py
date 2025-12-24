from database import SessionLocal, engine
from models import Base, Channels
import uvicorn
from server import app

def prepare_environment():
    Base.metadata.create_all(bind=engine)

    hls_base_folder = "hls_channels"
    import os
    if not os.path.exists(hls_base_folder):
        os.makedirs(hls_base_folder)

    media_folder = "media"
    if not os.path.exists(media_folder):
        os.makedirs(media_folder)
        print(f"⚠️ Pasta de mídia criada: {media_folder}. Coloque arquivos de mídia para teste.")

def main():
    prepare_environment()
    print("🚀 Servidor HTTP iniciado em http://0.0.0.0:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
