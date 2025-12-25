import os
import time
import threading
from datetime import datetime, timezone
from database import SessionLocal
from models import Channels, ChannelSchedule, Playlist, PlaylistItem, MediaItem
from player import Player

class ChannelRuntime:
    def __init__(self, channel, hls_base_folder="hls_channels"):
        self.channel = channel
        self.db = SessionLocal()
        self.player = Player()
        self.hls_base_folder = hls_base_folder

        self.channel_folder = os.path.join(
            self.hls_base_folder, f"channel_{self.channel.id}"
        )
        os.makedirs(self.channel_folder, exist_ok=True)

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.stop_signal = False

    def start_thread(self):
        if not self.thread.is_alive():
            self.thread.start()

    def stop_thread(self):
        self.stop_signal = True
        self.player.stop()

    # ---------------- TIMELINE / SEGMENTS ----------------

    def build_segments(self, episode, is_first: bool, is_last: bool):
        skips = episode.skips or {}
        cuts = skips.get("cuts", [])
        cut_ranges = sorted(
            [(episode.hms_to_seconds(c["start"]), episode.hms_to_seconds(c["end"])) for c in cuts]
        )

        segments = []
        cursor = 0.0
        for start, end in cut_ranges:
            if cursor < start:
                segments.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < episode.duration:
            segments.append((cursor, episode.duration))

        start_cut, end_cut = episode.get_cut_times(is_first, is_last)
        final_segments = []
        for s, e in segments:
            s_new = max(s, start_cut)
            e_new = min(e, end_cut)
            if s_new < e_new:
                final_segments.append((s_new, e_new))

        return final_segments

    def effective_duration(self, segments):
        return sum(end - start for start, end in segments)

    def resolve_offset(self, segments, offset):
        acc = 0.0
        for start, end in segments:
            seg_len = end - start
            if offset < acc + seg_len:
                return start + (offset - acc)
            acc += seg_len
        return 0.0

    # ---------------- PLAYLIST / EPISODES ----------------

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

    def resolve_playlist_items(self, playlist):
        items = (
            self.db.query(PlaylistItem, MediaItem)
            .join(MediaItem, MediaItem.id == PlaylistItem.media_id)
            .filter(PlaylistItem.playlist_id == playlist.id)
            .all()
        )
        media_items = [ep for _, ep in items]
        import random
        if playlist.shuffle:
            random.shuffle(media_items)
        return media_items

    # ---------------- MAIN RUN ----------------

    def run(self):
        while not self.stop_signal:
            schedule = self.get_active_schedule()
            if not schedule:
                time.sleep(5)
                continue

            playlist = self.db.get(Playlist, schedule.playlist_id)
            if not playlist:
                time.sleep(5)
                continue

            items = self.resolve_playlist_items(playlist)
            if not items:
                time.sleep(5)
                continue

            # Calcula offset com base na criação do canal (persistência)
            now = datetime.now(timezone.utc)
            channel_offset = int((now - self.channel.created_at).total_seconds())

            acc_duration = 0
            timeline = []
            for i, ep in enumerate(items):
                is_first = i == 0
                is_last = i == len(items) - 1
                segments = self.build_segments(ep, is_first, is_last)
                duration = self.effective_duration(segments)
                timeline.append({
                    "media": ep,
                    "segments": segments,
                    "duration": duration,
                    "is_first": is_first,
                    "is_last": is_last
                })
                acc_duration += duration

            if acc_duration == 0:
                time.sleep(5)
                continue

            # Calcula o ponto de reprodução atual
            pos = channel_offset % acc_duration
            idx = 0
            elapsed = 0
            for i, slot in enumerate(timeline):
                if elapsed + slot["duration"] > pos:
                    idx = i
                    internal_offset = pos - elapsed
                    break
                elapsed += slot["duration"]

            # Loop contínuo pelos episódios
            while not self.stop_signal:
                slot = timeline[idx]
                ep = slot["media"]
                start_time = self.resolve_offset(slot["segments"], internal_offset)
                print(f"[Channel {self.channel.id}] Iniciando: {ep.name}")

                # Inicia FFmpeg full live
                self.player.start(ep.file, self.channel_folder, start_time)
                self.player.process.wait()  # espera terminar antes de passar para o próximo

                print(f"[Channel {self.channel.id}] Episódio finalizado: {ep.name}")

                # próximo episódio
                idx = (idx + 1) % len(timeline)
                internal_offset = 0