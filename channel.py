import threading
import time
import os
from datetime import datetime, timezone

from database import SessionLocal
from models import ChannelSchedule, Playlist, MediaItem
from timeline import build_segments, resolve_offset, effective_duration
from player import Player


class ChannelRuntime:
    def __init__(self, channel, hls_base_folder="hls_channels"):
        self.channel = channel
        self.db = SessionLocal()
        self.player = Player()

        self.hls_path = os.path.join(
            hls_base_folder,
            f"channel_{channel.id}"
        )
        os.makedirs(self.hls_path, exist_ok=True)

        self.thread = None
        self.running = False

    # -----------------------------
    # PUBLIC
    # -----------------------------

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.player.stop()

    # -----------------------------
    # CORE LOOP
    # -----------------------------

    def run(self):
        print(f"[Channel {self.channel.id}] Worker iniciado")

        while self.running:
            try:
                playlist = self.get_active_playlist()
                if not playlist:
                    time.sleep(1)
                    continue

                items = self.get_playlist_items(playlist)
                if not items:
                    time.sleep(1)
                    continue

                # ⏱ calcula offset global do canal
                offset = self.get_channel_offset()

                # 🎯 encontra episódio atual
                slot, start_time = self.resolve_episode(items, offset)
                if not slot:
                    time.sleep(1)
                    continue

                media = slot["media"]
                print(f"[Channel {self.channel.id}] Iniciando: {media.name}")

                # ▶ inicia player
                try:
                    self.player.start(media.file, self.hls_path, start_time)
                    print(f"[Channel {self.channel.id}] FFmpeg iniciado: {media.name}")
                except Exception as e:
                    print(f"[Channel {self.channel.id}] Erro ao iniciar FFmpeg: {e}")
                    time.sleep(2)
                    continue

                # ⏳ monitora episódio até terminar
                while self.player.is_running() and self.running:
                    time.sleep(0.5)

                print(f"[Channel {self.channel.id}] Episódio finalizado: {media.name}")

            except Exception as e:
                print(f"[Channel {self.channel.id}] Erro no loop: {e}")
                time.sleep(2)
    # -----------------------------
    # HELPERS
    # -----------------------------

    def get_active_playlist(self):
        now = datetime.now().time()

        schedules = (
            self.db.query(ChannelSchedule)
            .filter(ChannelSchedule.channel_id == self.channel.id)
            .all()
        )

        for sch in schedules:
            if sch.start_time <= now <= sch.end_time:
                return self.db.get(Playlist, sch.playlist_id)

        return None

    def get_playlist_items(self, playlist):
        items = (
            self.db.query(MediaItem)
            .join(Playlist, Playlist.id == playlist.id)
            .all()
        )

        return items

    def get_channel_offset(self):
        now = datetime.now(timezone.utc)
        return int((now - self.channel.created_at).total_seconds())

    def resolve_episode(self, items, channel_offset):
        timeline = []
        acc = 0

        for i, ep in enumerate(items):
            is_first = i == 0
            is_last = i == len(items) - 1

            segments = build_segments(ep, is_first, is_last)
            duration = effective_duration(segments)

            timeline.append({
                "media": ep,
                "start": acc,
                "end": acc + duration,
                "duration": duration,
                "segments": segments,
            })

            acc += duration

        if acc == 0:
            return None, None

        pos = channel_offset % acc

        for slot in timeline:
            if slot["start"] <= pos < slot["end"]:
                offset = resolve_offset(slot["segments"], pos - slot["start"])
                slot["start_offset"] = offset
                return slot, offset

        return None, None