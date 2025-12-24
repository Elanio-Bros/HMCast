import threading
from database import SessionLocal, engine
from models import Base, Channels
from channel import ChannelRuntime
import uvicorn
import os

def start_channels():
    db = SessionLocal()
    channels = db.query(Channels).all()
    db.close()

    for channel in channels:
        runtime = ChannelRuntime(channel)
        t = threading.Thread(target=runtime.run, daemon=True)
        t.start()
        print(f"📡 Thread iniciada para canal: {channel.name}")

def prepare_environment():
    # Cria tabelas
    Base.metadata.create_all(bind=engine)

    # Cria pasta base de HLS
    hls_base_folder = "hls_channels"
    if not os.path.exists(hls_base_folder):
        os.makedirs(hls_base_folder)

    # Cria pasta de mídia de exemplo
    media_folder = "media"
    if not os.path.exists(media_folder):
        os.makedirs(media_folder)
        print(f"⚠️ Pasta de mídia criada: {media_folder}. Coloque arquivos de vídeo para teste.")

def main():
    prepare_environment()
    start_channels()

    print("🚀 Servidor HTTP iniciado em http://0.0.0.0:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
