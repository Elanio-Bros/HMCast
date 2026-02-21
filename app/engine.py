import os
import time
import threading
import asyncio
import shutil
from fastapi import HTTPException

from .database import SessionLocal
from .models import Channels, MediaFolder
from .channel import ChannelRuntime
from .media_utils import MediaUtils

HLS_BASE = "hls"
os.makedirs(HLS_BASE, exist_ok=True)

# Timeout configurável para aquecimento da playlist (segundos)
PLAYLIST_WARMUP_TIMEOUT = float(os.getenv("HLS_PLAYLIST_WARMUP_TIMEOUT", "15"))

channel_runtimes: dict[int, ChannelRuntime] = {}
_channel_lock = threading.Lock()

def startup_logic():
    """Lógica de inicialização do motor (limpeza e canais ALWAYS_ON)"""
    print("[Engine] Iniciando core engine...")
    print("[Engine] Limpando arquivos HLS residuais...")
    try:
        if os.path.exists(HLS_BASE):
            for it in os.listdir(HLS_BASE):
                it_path = os.path.join(HLS_BASE, it)
                if os.path.isdir(it_path):
                    shutil.rmtree(it_path)
                else:
                    os.remove(it_path)
    except Exception as e:
        print(f"[Engine] Erro ao limpar HLS_BASE: {e}")

    print("[Engine] Verificando canais ALWAYS_ON...")
    db = SessionLocal()
    try:
        always_on_channels = db.query(Channels).filter(Channels.execution_mode == "ALWAYS_ON").all()
        for ch in always_on_channels:
            print(f"[Engine] Iniciando canal fixo: {ch.name}")
            ensure_channel_running(ch.id)
            time.sleep(1)
    except Exception as e:
        print(f"[Engine] Erro no startup_logic: {e}")
    finally:
        db.close()

def shutdown_logic():
    """Lógica de encerramento do motor"""
    print("[Engine] Desligando core engine...")
    for cid, runtime in list(channel_runtimes.items()):
        try:
            runtime.stop()
        except Exception:
            pass

async def background_warmup_worker():
    """Tarefa que pré-renderiza canais PREDICTIVE periodicamente"""
    while True:
        # Pega intervalo e espera
        interval = int(os.getenv("PREDICTIVE_WARMUP_INTERVAL", "300"))
        await asyncio.sleep(interval)
        
        print("[Engine] Ciclo de Warmup para canais PREDICTIVE...")
        db = SessionLocal()
        try:
            channels = db.query(Channels).filter(Channels.execution_mode == "PREDICTIVE").all()
            for ch in channels:
                runtime = channel_runtimes.get(ch.id)
                if not runtime or not runtime.running:
                    print(f"[Engine] Warmup: Pré-renderizando canal {ch.name}...")
                    ensure_channel_running(ch.id, is_warmup=True)
        except Exception as e:
            print(f"[Engine] Erro no warmup worker: {e}")
        finally:
            db.close()

async def background_media_scanner():
    """Tarefa que escaneia pastas de mídia periodicamente"""
    scanner = MediaUtils()
    while True:
        # Pega intervalo (default 10 min)
        interval = int(os.getenv("MEDIA_AUTO_SCAN_INTERVAL", "600"))
        
        print("[Engine] Iniciando ciclo de Auto-Scan de mídias...")
        db = SessionLocal()
        try:
            folders = db.query(MediaFolder).all()
            for f in folders:
                print(f"[Engine] Escaneando: {f.path}")
                scanner.scan_media_folder(f.path)
        except Exception as e:
            print(f"[Engine] Erro no media scanner worker: {e}")
        finally:
            db.close()
            
        await asyncio.sleep(interval)

def ensure_channel_running(channel_id: int, is_warmup: bool = False) -> ChannelRuntime:
    """Garante que um canal está rodando, iniciando-o se necessário"""
    with _channel_lock:
        runtime = channel_runtimes.get(channel_id)
        if runtime and runtime.thread and runtime.thread.is_alive() and runtime.running:
            if not is_warmup:
                runtime.touch()
            return runtime

        if runtime:
            try:
                runtime.stop()
            except:
                pass

        db = SessionLocal()
        channel = db.get(Channels, channel_id)
        db.close()

        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        runtime = ChannelRuntime(channel, HLS_BASE)
        if not is_warmup:
            runtime.touch()
        
        runtime.start()
        channel_runtimes[channel_id] = runtime
        return runtime
