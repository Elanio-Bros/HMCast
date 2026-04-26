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

    def hms_to_seconds(self, hms: str) -> float:
        if not hms:
            return 0.0

        is_negative = False
        if str(hms).startswith("-"):
            is_negative = True
            hms = hms[1:]

        hms = hms.replace(',', '.')
        parts = str(hms).split(':')
        
        try:
            val = 0.0
            if len(parts) == 3: # HH:MM:SS
                h, m, s = parts
                val = int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2: # MM:SS
                m, s = parts
                val = int(m) * 60 + float(s)
            elif len(parts) == 1: # SS
                val = float(parts[0])
            else:
                raise ValueError
            
            final_val = -val if is_negative else val
            
            # Resolução absoluta se for negativo
            if final_val < 0:
                return max(0.0, float(self.duration) + final_val)
            
            # Caso especial: -00:00:00 significa "fim do arquivo"
            if is_negative and val == 0:
                return float(self.duration)

            return final_val
        except (ValueError, TypeError):
            return 0.0

    def get_cut_times(self, is_first: bool, is_last: bool):
        start = 0.0
        end = float(self.duration)

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
    identifier = Column(String, unique=True, nullable=True) # Código personalizado (slug)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, default="TV")  # "TV" ou "RADIO"
    execution_mode = Column(String, nullable=False, default="ON_DEMAND") # "ALWAYS_ON", "ON_DEMAND", "PREDICTIVE"
    active = Column(Boolean, default=True)
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
    position = Column(Integer, default=0)
    role = Column(String, default="CONTENT")  # "OPENING", "CONTENT", "CLOSING"
