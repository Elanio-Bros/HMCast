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

    def resolve_playlist_episodes(self, playlist):
        items = (
            self.db.query(PlaylistItem, MediaItem)
            .join(MediaItem, MediaItem.id == PlaylistItem.media_id)
            .filter(PlaylistItem.playlist_id == playlist.id)
            .all()
        )

        episodes = [ep for _, ep in items]

        if playlist.shuffle:
            import random
            random.shuffle(episodes)

        return episodes

    def resolve_episode_by_time(self, episodes, channel_offset):
        timeline = []
        acc = 0

        for i, ep in enumerate(episodes):
            prev_ep = episodes[i - 1] if i > 0 else None
            next_ep = episodes[i + 1] if i < len(episodes) - 1 else None

            is_first = prev_ep is None or prev_ep.series != ep.series
            is_last = next_ep is None or next_ep.series != ep.series

            segments = build_segments(ep, is_first, is_last)
            duration = effective_duration(segments)

            timeline.append({
                "episode": ep,
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

    def cleanup_old_episodes(self, keep_media_id):
        channel_folder = os.path.join(
            self.hls_base_folder, f"channel_{self.channel.id}"
        )
        if not os.path.exists(channel_folder):
            return

        for folder in os.listdir(channel_folder):
            if f"episode_{keep_media_id}" not in folder:
                shutil.rmtree(
                    os.path.join(channel_folder, folder),
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
            episodes = self.resolve_playlist_episodes(playlist)

            if not episodes:
                self.player.play_off_air()
                time.sleep(5)
                continue

            now = datetime.now(timezone.utc)
            channel_offset = int(
                (now - self.channel.created_at).total_seconds()
            )

            slot, start_time = self.resolve_episode_by_time(
                episodes, channel_offset
            )

            if not slot:
                self.player.play_off_air()
                time.sleep(5)
                continue

            ep = slot["episode"]

            if not os.path.exists(ep.file):
                print(f"❌ Arquivo não encontrado: {ep.file}")
                time.sleep(5)
                continue

            ep_folder = os.path.join(
                self.hls_base_folder,
                f"channel_{self.channel.id}",
                f"episode_{ep.id}"
            )

            os.makedirs(ep_folder, exist_ok=True)
            self.cleanup_old_episodes(ep.id)

            print(
                f"▶️ {ep.name} | start={start_time}s"
            )
            
            self.player.generate_hls(ep.file, ep_folder)
            time.sleep(5)