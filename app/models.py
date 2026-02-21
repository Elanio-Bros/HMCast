from sqlalchemy import (
    Column, Integer, String, JSON, DateTime,
    Time, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, validates, reconstructor,relationship
from datetime import datetime, timezone

import re

Base = declarative_base()


class MediaFolder(Base):
    __tablename__ = "media_folders"

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=True, unique=True)
    name = Column(String, nullable=False)


class MediaItem(Base):
    __tablename__ = "media_item"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    file = Column(String, nullable=False)
    # duração total do arquivo em segundos
    duration = Column(Integer, nullable=False)
    folder_id = Column(Integer, ForeignKey("media_folders.id"), nullable=True)
    sequence_id = Column(Integer, ForeignKey("media_item.id"), nullable=True)
    skips = Column(JSON, nullable=True)  # { intro:{}, finish:{}, cuts:[] }

    @staticmethod
    def hms_to_seconds(hms: str) -> float:
        if not hms:
            return 0.0

        if hms.startswith("-"):
             # Valores negativos (sentinelas) devem ser tratados pela lógica chamadora
             return 0.0

        hms = hms.replace(',', '.')
        # Tenta splitar por ':'
        parts = hms.split(':')
        
        try:
            if len(parts) == 3: # HH:MM:SS
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2: # MM:SS
                m, s = parts
                return int(m) * 60 + float(s)
            elif len(parts) == 1: # SS
                return float(parts[0])
            else:
                raise ValueError
        except (ValueError, TypeError):
            print(f"[Models] Formato de tempo inválido: {hms}")
            return 0.0

    def get_cut_times(self, is_first: bool, is_last: bool):
        start = 0
        end = self.duration

        skips = self.skips or {}
        intro = skips.get("intro")
        finish = skips.get("finish")

        if intro and not is_first:
            start = self.hms_to_seconds(intro["end"])

        if finish and not is_last:
            end = self.hms_to_seconds(finish["start"])

        return start, end


class Channels(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, default="TV")  # "TV" ou "RADIO"
    execution_mode = Column(String, nullable=False, default="ON_DEMAND") # "ALWAYS_ON", "ON_DEMAND", "PREDICTIVE"
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
    media_id = Column(Integer, ForeignKey("media_item.id"))
