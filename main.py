from database import engine
from models import Base
import os
import uvicorn


def prepare_environment():
    # Cria tabelas
    Base.metadata.create_all(bind=engine)

    # Cria pastas
    os.makedirs("hls_channels", exist_ok=True)


if __name__ == "__main__":
    prepare_environment()
    print("🚀 Servidor HTTP iniciado em http://0.0.0.0:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
