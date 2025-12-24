from sqlalchemy import (
    Column, Integer, String, JSON, DateTime,
    Time, ForeignKey, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

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
    duration = Column(Integer, nullable=False)  # duração total do arquivo
    series = Column(String, nullable=True)
    sequence_group = Column(String, nullable=True)
    skips = Column(JSON, nullable=True)  # { intro:{}, finish:{}, cuts:[] }
    folder_id = Column(Integer, ForeignKey("media_folders.id"), nullable=False)

    # ---------- helpers ----------
    @staticmethod
    def hms_to_seconds(hms: str) -> int:
        h, m, s = map(int, hms.split(":"))
        return h * 3600 + m * 60 + s

    def get_cut_times(self, is_first: bool, is_last: bool):
        """
        Retorna (start, end) em segundos considerando intro e finish
        """
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

    def effective_duration(self, is_first: bool, is_last: bool) -> int:
        start, end = self.get_cut_times(is_first, is_last)
        return max(0, end - start)


class Channels(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now().astimezone())


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
