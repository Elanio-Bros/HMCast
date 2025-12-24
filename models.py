from sqlalchemy import (
    Column, Integer, String, JSON, DateTime,
    Time, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, validates, reconstructor
from datetime import datetime, timezone

import re

Base = declarative_base()


class MediaFolder(Base):
    __tablename__ = "media_folders"

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=True)


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    file = Column(String, nullable=False)
    # duração total do arquivo em segundos
    duration = Column(Integer, nullable=False)
    series = Column(String, nullable=True)
    sequence_group = Column(String, nullable=True)
    skips = Column(JSON, nullable=True)  # { intro:{}, finish:{}, cuts:[] }

    @staticmethod
    def hms_to_seconds(hms: str) -> float:
        if not hms:
            return 0.0

        if hms.startswith("-"):
            raise ValueError(
                f"Sentinel '{hms}' não representa tempo válido. "
                "Este valor deve ser tratado pela regra de negócio."
            )

        hms = hms.replace(',', '.')
        pattern = r'^(\d+):([0-5]\d):([0-5]\d(?:\.\d+)?)$'
        match = re.match(pattern, hms)

        if not match:
            raise ValueError(f"Formato inválido de tempo: {hms}")

        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)

    def get_cut_times(self, is_first: bool, is_last: bool):
        start = 0
        end = self.duration

        skips = self.skips or {}
        intro = skips.get("intro")
        finish = skips.get("finish")

        if intro and not is_first:
            start = self.hms_to_seconds(intro["end"])

        if finish and not is_last:
            finish_end = finish.get("end")
            if finish_end == "-00:00:00":
                end = self.duration
            else:
                end = self.hms_to_seconds(finish["start"])

        return start, end

    def effective_duration(self, is_first: bool, is_last: bool) -> float:
        start, end = self.get_cut_times(is_first, is_last)
        return max(0, end - start)


class Channels(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    @validates("created_at")
    def _validate_created_at(self, key, value):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @reconstructor
    def init_on_load(self):
        if self.created_at and self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)


class ChannelSchedule(Base):
    __tablename__ = "channel_schedules"

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    weekdays = Column(JSON, nullable=True)
    month_days = Column(JSON, nullable=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    shuffle = Column(Boolean, default=False)


class PlaylistItem(Base):
    __tablename__ = "playlist_items"

    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    episode_id = Column(Integer, ForeignKey("episodes.id"))
