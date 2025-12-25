import os
from datetime import datetime, timezone
from database import SessionLocal
from models import Playlist, PlaylistItem, MediaItem, ChannelSchedule
from timeline import build_segments, resolve_offset, effective_duration
from player import Player

class ChannelRuntime:
    def __init__(self, channel, hls_base_folder="hls_channels"):
        self.channel = channel
        self.db = SessionLocal()
        self.player = Player()
        self.hls_base_folder = hls_base_folder

        # Pasta do canal
        self.channel_folder = os.path.join(
            self.hls_base_folder, f"channel_{self.channel.id}"
        )
        os.makedirs(self.channel_folder, exist_ok=True)

    # -------------------------------
    # Schedules e Playlist
    # -------------------------------
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

        if playlist.shuffle:
            import random
            random.shuffle(media_items)

        return media_items

    # -------------------------------
    # Timeline contínua
    # -------------------------------
    def resolve_episode_by_time(self, items, channel_offset):
        timeline = []
        acc = 0

        for i, ep in enumerate(items):
            prev_ep = items[i - 1] if i > 0 else None
            next_ep = items[i + 1] if i < len(items) - 1 else None

            is_first = prev_ep is None or prev_ep.series != ep.series
            is_last = next_ep is None or next_ep.series != ep.series

            segments = build_segments(ep, is_first, is_last)
            duration = effective_duration(segments)

            timeline.append({
                "media": ep,
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

    # -------------------------------
    # Cleanup
    # -------------------------------
    def cleanup_old_media(self):
        """
        Remove arquivos antigos, mantendo apenas o atual.
        """
        if not os.path.exists(self.channel_folder):
            return

        for f in os.listdir(self.channel_folder):
            full_path = os.path.join(self.channel_folder, f)
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
            except Exception:
                pass

    # -------------------------------
    # Método principal on-demand
    # -------------------------------
    def get_current_master(self):
        """
        Resolve o episódio ativo e gera HLS on-demand.
        """
        schedule = self.get_active_schedule()
        if not schedule:
            # Fora do ar → retorna off_air
            return self.player.play_off_air()

        playlist = self.db.get(Playlist, schedule.playlist_id)
        if not playlist:
            return self.player.play_off_air()

        items = self.resolve_playlist_items(playlist)
        if not items:
            return self.player.play_off_air()

        now = datetime.now(timezone.utc)
        channel_offset = int((now - self.channel.created_at).total_seconds())

        slot, start_time = self.resolve_episode_by_time(items, channel_offset)
        if not slot:
            return self.player.play_off_air()

        media_item = slot["media"]
        if not os.path.exists(media_item.file):
            return self.player.play_off_air()

        # Gera HLS direto na pasta do canal
        master_path = self.player.generate_live_hls(media_item.file, self.channel_folder,self.channel.id)
        return master_path