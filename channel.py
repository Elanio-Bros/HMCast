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

    def build_segments(self, media, is_first: bool, is_last: bool):
        skips = media.skips or {}
        # print(media)
        duration = media.duration
        forbidden = []

        # --- INTRO ---
        intro = skips.get("intro")
        if intro and not is_first:
            forbidden.append((
                media.hms_to_seconds(intro["start"]),
                media.hms_to_seconds(intro["end"])
            ))

        # --- FINISH ---
        finish = skips.get("finish")
        if finish and not is_last:
            forbidden.append((
                media.hms_to_seconds(finish["start"]),
                (duration if finish['end'] == '-00:00:00' else media.hms_to_seconds(finish["end"]))
            ))

        # --- CUTS ---
        for cut in skips.get("cuts", []):
            forbidden.append((
                media.hms_to_seconds(cut["start"]),
                media.hms_to_seconds(cut["end"])
            ))

        # Ordena tudo
        forbidden.sort()

        # Agora constrói os segmentos válidos
        segments = []
        cursor = 0.0

        for start, end in forbidden:
            if cursor < start:
                segments.append((cursor, start))
            cursor = max(cursor, end)

        if cursor < duration:
            segments.append((cursor, duration))

        return segments

    def effective_duration(self, segments):
        return sum(end - start for start, end in segments)

    def resolve_offset(self, segments, internal_offset):
        acc = 0.0
        for start, end in segments:
            seg_len = end - start

            if internal_offset < acc + seg_len:
                offset_inside = internal_offset - acc
                start_time = start + offset_inside
                play_duration = end - start_time
                return start_time, play_duration

            acc += seg_len

        return None, None

    # ---------------- PLAYLIST / MEDIAS ----------------

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
        media_items = [media for _, media in items]
        import random
        if playlist.shuffle:
            random.shuffle(media_items)
        return media_items

    def cleanup_old_segments(self):
        def worker():
            if not os.path.exists(self.channel_folder):
                return

            ts_files = [f for f in os.listdir(
                self.channel_folder) if f.endswith(".ts")]
            referenced_files = set()

            # coleta os arquivos .ts ainda referenciados nas playlists
            for file in os.listdir(self.channel_folder):
                if file.endswith(".m3u8"):
                    try:
                        with open(os.path.join(self.channel_folder, file), "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if line.endswith(".ts"):
                                    referenced_files.add(line)
                    except Exception as e:
                        print(
                            f"[Channel {self.channel.id}] Erro ao ler {file}: {e}")

            # remove os segmentos que não estão mais na playlist
            for ts in ts_files:
                if ts not in referenced_files:
                    try:
                        os.remove(os.path.join(self.channel_folder, ts))
                        print(
                            f"[Channel {self.channel.id}] Removido segmento antigo: {ts}")
                    except Exception as e:
                        print(
                            f"[Channel {self.channel.id}] Erro ao remover {ts}: {e}")

        threading.Thread(target=worker, daemon=True).start()
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
            
            for i, media in enumerate(items):
                
                is_first = i == 0
                is_last = i == len(items) - 1
                segments = self.build_segments(media, is_first, is_last)
                duration = self.effective_duration(segments)
                timeline.append({
                    "media": media,
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
            
            
            # Loop contínuo
            while not self.stop_signal:
                slot = timeline[idx]
                ep = slot["media"]

                start_time, play_duration = self.resolve_offset(
                    slot["segments"],
                    internal_offset
                )

                print(f"[Channel {self.channel.id}] Iniciando: {ep.name}")
                print(f"Start: {start_time}s | Duration: {play_duration}s")

                self.player.start(
                    ep.file,
                    self.channel_folder,
                    start_time,
                    play_duration
                )

                self.player.process.wait()

                print(f"[Channel {self.channel.id}] Episódio finalizado: {ep.name}")
                self.cleanup_old_segments()

                # Próximo episódio
                idx = (idx + 1) % len(timeline)
                internal_offset = 0
