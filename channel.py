import os
import time
import shutil
from datetime import datetime, timezone

from database import SessionLocal
from models import Playlist, PlaylistItem, MediaItem, ChannelSchedule
from timeline import build_segments, resolve_offset, effective_duration
from player import Player
from media_utils import MediaUtils

class ChannelRuntime:
    def __init__(self, channel, hls_base_folder="hls_channels"):
        self.channel = channel
        self.db = SessionLocal()
        self.player = Player()
        self.media = MediaUtils()

        self.hls_base_folder = hls_base_folder
        os.makedirs(self.hls_base_folder, exist_ok=True)

        self.current_folder = os.path.join(
            self.hls_base_folder,
            f"channel_{self.channel.id}",
            "current"
        )
        os.makedirs(self.current_folder, exist_ok=True)

        self.current_media_id = None
        
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
            self.db.query(PlaylistItem, MediaItem)
            .join(MediaItem, MediaItem.id == PlaylistItem.episode_id)
            .filter(PlaylistItem.playlist_id == playlist.id)
            .all()
        )

        media_items = [m for _, m in items]

        if playlist.shuffle:
            import random
            random.shuffle(media_items)

        return media_items

    def resolve_media_by_time(self, media_items, channel_offset):
        timeline = []
        acc = 0

        for i, media in enumerate(media_items):
            prev_media = media_items[i - 1] if i > 0 else None
            next_media = media_items[i + 1] if i < len(media_items) - 1 else None

            is_first = prev_media is None or prev_media.series != getattr(media, "series", None)
            is_last = next_media is None or next_media.series != getattr(media, "series", None)

            segments = build_segments(media, is_first, is_last)
            duration = effective_duration(segments)

            timeline.append({
                "media": media,
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

    def cleanup_old_media(self, keep_media_id):
        for folder in os.listdir(self.current_folder):
            if f"media_{keep_media_id}" not in folder:
                shutil.rmtree(
                    os.path.join(self.current_folder, folder),
                    ignore_errors=True
                )

    def run(self):
        print(f"📺 Canal '{self.channel.name}' iniciado")

        while True:
            schedule = self.get_active_schedule()
            if not schedule:
                print("⛔ Fora do ar")
                self.player.play_off_air()
                time.sleep(5)
                continue

            playlist = self.db.get(Playlist, schedule.playlist_id)
            media_items = self.resolve_playlist_media(playlist)

            if not media_items:
                self.player.play_off_air()
                time.sleep(5)
                continue

            now = datetime.now(timezone.utc)
            channel_offset = int((now - self.channel.created_at).total_seconds())

            slot, start_time = self.resolve_media_by_time(media_items, channel_offset)
            if not slot:
                self.player.play_off_air()
                time.sleep(5)
                continue

            media = slot["media"]

            if not os.path.exists(media.file):
                print(f"❌ Arquivo não encontrado: {media.file}")
                time.sleep(5)
                continue

            if self.current_media_id != media.id:
                self.player.generate_live_hls(media.file, self.current_folder, start_time)
                self.current_media_id = media.id

            time.sleep(5)