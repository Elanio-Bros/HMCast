import time
from datetime import datetime
import os
import subprocess
from database import SessionLocal
from models import Playlist, PlaylistItem, Episode, ChannelSchedule

class ChannelRuntime:
    def __init__(self, channel):
        self.channel = channel
        self.db = SessionLocal()

    def get_active_schedule(self):
        now = datetime.now().astimezone()
        now_time = now.time()
        weekday = now.weekday()
        month_day = now.day

        schedules = (
            self.db.query(ChannelSchedule)
            .filter(ChannelSchedule.channel_id == self.channel.id)
            .order_by(ChannelSchedule.id)
            .all()
        )

        active_schedules = []
        for sch in schedules:
            if not (sch.start_time <= now_time <= sch.end_time):
                continue
            if sch.weekdays and weekday not in sch.weekdays:
                continue
            if sch.month_days and month_day not in sch.month_days:
                continue
            active_schedules.append(sch)

        return active_schedules[0] if active_schedules else None

    def resolve_playlist_episodes(self, playlist):
        items = (
            self.db.query(PlaylistItem, Episode)
            .join(Episode, Episode.id == PlaylistItem.episode_id)
            .filter(PlaylistItem.playlist_id == playlist.id)
            .all()
        )

        episodes = [ep for _, ep in items]

        if playlist.shuffle:
            groups = {}
            for ep in episodes:
                key = ep.sequence_group or f"single_{ep.id}"
                groups.setdefault(key, []).append(ep)

            group_list = list(groups.values())
            import random
            random.shuffle(group_list)
            episodes = [ep for g in group_list for ep in g]

        return episodes

    def resolve_episode_by_time(self, episodes, channel_offset):
        from timeline import build_segments, resolve_offset, effective_duration

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

        total = acc
        pos = channel_offset % total if total > 0 else 0

        for slot in timeline:
            if slot["start"] <= pos < slot["end"]:
                internal_offset = pos - slot["start"]
                start_time = resolve_offset(slot["segments"], internal_offset)
                return slot, start_time

        return None, None

    def play_black_screen(self, duration: int = 5, off_air_image: str = "off_air.png"):
        cmd = []
        if off_air_image and os.path.exists(off_air_image):
            cmd = [
                "ffmpeg",
                "-loop", "1",
                "-i", off_air_image,
                "-t", str(duration),
                "-f", "mpegts",
                "pipe:1"
            ]
        else:
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c=black:s=1280x720:d={duration}",
                "-f", "mpegts",
                "pipe:1"
            ]
        subprocess.run(cmd)

    def run(self):
        print(f"📺 Canal '{self.channel.name}' iniciado")

        while True:
            schedule = self.get_active_schedule()
            if not schedule:
                print("⛔ Fora do ar (sem schedule ativo)")
                self.play_black_screen(duration=5)
                time.sleep(5)
                continue

            playlist = self.db.get(Playlist, schedule.playlist_id)
            episodes = self.resolve_playlist_episodes(playlist)

            if not episodes:
                print("📭 Playlist vazia")
                self.play_black_screen(duration=5)
                time.sleep(5)
                continue

            channel_offset = int(
                (datetime.now().astimezone() - self.channel.created_at).total_seconds()
            )

            slot, start_time = self.resolve_episode_by_time(episodes, channel_offset)

            if not slot or start_time is None:
                print("⛔ Nenhum episódio disponível no momento")
                self.play_black_screen(duration=5)
                time.sleep(5)
                continue

            ep = slot["episode"]

            print(
                f"▶️ {ep.name} | "
                f"start={start_time}s | "
                f"first={slot['is_first']} last={slot['is_last']}"
            )

            time.sleep(5)