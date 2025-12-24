import os
import time
from datetime import datetime, timezone
import threading

from database import SessionLocal
from models import Playlist, PlaylistItem, Media, ChannelSchedule
from timeline import build_segments, resolve_offset, effective_duration
from player import Player
from media_utils import MediaUtils
import server

class ChannelRuntime:
    def __init__(self, channel, hls_base_folder="hls_channels"):
        self.channel = channel
        self.db = SessionLocal()
        self.player = Player()
        self.media_utils = MediaUtils()

        self.hls_base_folder = hls_base_folder
        self.current_folder = os.path.join(
            self.hls_base_folder, f"channel_{self.channel.id}", "current"
        )
        os.makedirs(self.current_folder, exist_ok=True)

        self.lock = threading.Lock() 

    def get_active_schedule(self):
        now = datetime.now().astimezone()
        now_time = now.time()
        weekday = now.weekday()
        month_day = now.day

        schedules = (
            self.db.query(ChannelSchedule)
            .filter(ChannelSchedule.channel_id == self.channel.id)
            .all()
        )

        for sch in schedules:
            if not (sch.start_time <= now_time <= sch.end_time):
                continue
            if sch.weekdays and weekday not in sch.weekdays:
                continue
            if sch.month_days and month_day not in sch.month_days:
                continue
            return sch
        return None

    def resolve_playlist_media(self, playlist):
        items = (
            self.db.query(PlaylistItem, Media)
            .join(Media, Media.id == PlaylistItem.media_id)
            .filter(PlaylistItem.playlist_id == playlist.id)
            .all()
        )
        medias = [m for _, m in items]
        if playlist.shuffle:
            import random
            random.shuffle(medias)
        return medias

    def resolve_media_by_time(self, medias, channel_offset):
        timeline = []
        acc = 0

        for i, m in enumerate(medias):
            prev = medias[i - 1] if i > 0 else None
            next_ = medias[i + 1] if i < len(medias) - 1 else None

            is_first = prev is None or prev.series != m.series
            is_last = next_ is None or next_.series != m.series

            segments = build_segments(m, is_first, is_last)
            duration = effective_duration(segments)

            timeline.append({
                "media": m,
                "start": acc,
                "end": acc + duration,
                "segments": segments,
                "is_first": is_first,
                "is_last": is_last
            })
            acc += duration

        if acc == 0:
            return None, None

        pos = channel_offset % acc

        for slot in timeline:
            if slot["start"] <= pos < slot["end"]:
                internal_offset = pos - slot["start"]
                start_time = resolve_offset(slot["segments"], internal_offset)
                return slot, start_time

        return None, None

    def cleanup_ts_segments(self):
        with self.lock:
            master_path = os.path.join(self.current_folder, "master.m3u8")
            if not os.path.exists(master_path):
                return

            with open(master_path, "r") as f:
                lines = f.readlines()
            ts_files_in_m3u8 = set([l.strip() for l in lines if l.endswith(".ts")])

            for f in os.listdir(self.current_folder):
                if f.endswith(".ts") and f not in ts_files_in_m3u8:
                    try:
                        os.remove(os.path.join(self.current_folder, f))
                    except:
                        pass

    def run(self):
        print(f"📺 Canal '{self.channel.name}' iniciado (HLS contínuo)")

        while True:
            last_ts = server.last_access.get(self.channel.id, time.time())
            if time.time() - last_ts > server.CHANNEL_TIMEOUT:
                print(f"⏹ Canal '{self.channel.name}' desligado por inatividade")
                if self.channel.id in server.active_channels:
                    del server.active_channels[self.channel.id]
                break
            
            schedule = self.get_active_schedule()
            if not schedule:
                self.player.play_off_air()
                time.sleep(5)
                continue

            playlist = self.db.get(Playlist, schedule.playlist_id)
            medias = self.resolve_playlist_media(playlist)
            if not medias:
                self.player.play_off_air()
                time.sleep(5)
                continue

            now = datetime.now(timezone.utc)
            channel_offset = int((now - self.channel.created_at).total_seconds())

            slot, start_time = self.resolve_media_by_time(medias, channel_offset)
            if not slot:
                self.player.play_off_air()
                time.sleep(5)
                continue

            media_item = slot["media"]
            if not os.path.exists(media_item.file):
                print(f"❌ Arquivo não encontrado: {media_item.file}")
                time.sleep(5)
                continue

            print(f"▶️ {media_item.name} | start={start_time}s")

            self.player.generate_live_hls(media_item.file, self.current_folder)

            self.cleanup_ts_segments()

            time.sleep(5)