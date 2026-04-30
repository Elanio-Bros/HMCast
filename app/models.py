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
    specific_dates = Column(JSON, nullable=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))

    @staticmethod
    def check_conflict(db, channel_id, start_t, end_t, weekdays=None, month_days=None, specific_dates=None):
        """Verifica conflitos de horário no Core do sistema, considerando deslocamento de dia em overnight."""
        from datetime import time, datetime, timedelta
        existing = db.query(ChannelSchedule).filter_by(channel_id=channel_id).all()
        
        def expand_sch(st, et, wds, mds, sds):
            # Retorna lista de (tipo, valor, start, end)
            slots = []
            is_overnight = st > et
            
            # Dias da semana
            if wds:
                wd_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                for wd in wds:
                    if not is_overnight:
                        slots.append(('WD', wd, st, et))
                    else:
                        slots.append(('WD', wd, st, time(23, 59, 59)))
                        next_wd = wd_names[(wd_names.index(wd) + 1) % 7]
                        slots.append(('WD', next_wd, time(0, 0, 0), et))
            
            # Dias do mês
            if mds:
                for md in mds:
                    if not is_overnight:
                        slots.append(('MD', md, st, et))
                    else:
                        slots.append(('MD', md, st, time(23, 59, 59)))
                        # Simplificação: md + 1 (não checa virada de mês, mas cobre a maioria dos casos)
                        slots.append(('MD', (md % 31) + 1, time(0, 0, 0), et))
            
            # Datas específicas
            if sds:
                for sd in sds:
                    if not is_overnight:
                        slots.append(('SD', sd, st, et))
                    else:
                        slots.append(('SD', sd, st, time(23, 59, 59)))
                        try:
                            # Tenta parsear a data para achar o dia seguinte
                            fmt = "%d/%m/%Y" if len(sd) > 5 else "%d/%m"
                            dt = datetime.strptime(sd, fmt)
                            next_dt = dt + timedelta(days=1)
                            slots.append(('SD', next_dt.strftime(fmt), time(0, 0, 0), et))
                        except: pass
            
            # Diário (Todo dia)
            if not (wds or mds or sds):
                if not is_overnight:
                    slots.append(('ALL', 'ALL', st, et))
                else:
                    # Overnight diário ocupa o fim e o início de TODOS os dias
                    slots.append(('ALL', 'ALL', st, time(23, 59, 59)))
                    slots.append(('ALL', 'ALL', time(0, 0, 0), et))
            
            return slots

        new_slots = expand_sch(start_t, end_t, weekdays, month_days, specific_dates)
        
        for sch in existing:
            sch_slots = expand_sch(sch.start_time, sch.end_time, sch.weekdays, sch.month_days, sch.specific_dates)
            
            for n_type, n_val, n_st, n_et in new_slots:
                for s_type, s_val, s_st, s_et in sch_slots:
                    # Só conflita se o "dia" bater ou um deles for 'ALL'
                    day_match = (n_type == s_type and n_val == s_val) or (n_type == 'ALL' or s_type == 'ALL')
                    
                    if day_match:
                        # Verifica sobreposição de tempo
                        if (n_st < s_et) and (n_et > s_st):
                            return f"Conflito no período {n_st.strftime('%H:%M')}-{n_et.strftime('%H:%M')} ({n_val})"
        
        return None


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    shuffle = Column(Boolean, default=False)

    @staticmethod
    def calc_total_duration(db, playlist_id: int) -> int:
        """Calcula a duração total da playlist considerando os cortes (skips)."""
        from .models import PlaylistItem, MediaItem
        items = db.query(PlaylistItem, MediaItem).join(MediaItem, MediaItem.id == PlaylistItem.media_id).filter(PlaylistItem.playlist_id == playlist_id).order_by(PlaylistItem.position).all()
        total = 0
        for i, (p_item, m_item) in enumerate(items):
            duration = float(m_item.duration)
            skips = m_item.skips or {}
            is_first = (i == 0)
            is_last = (i == len(items) - 1)
            
            # Se não for o primeiro item, ignora a intro
            if "intro" in skips and not is_first:
                st = m_item.hms_to_seconds(skips["intro"]["start"])
                et = m_item.hms_to_seconds(skips["intro"]["end"])
                duration -= max(0, et - st)
            
            # Se não for o último item, ignora o final
            if "finish" in skips and not is_last:
                st = m_item.hms_to_seconds(skips["finish"]["start"])
                et = float(m_item.duration)
                duration -= max(0, et - st)
                
            if "cuts" in skips:
                for cut in skips.get("cuts", []):
                    st = m_item.hms_to_seconds(cut["start"])
                    et = m_item.hms_to_seconds(cut["end"])
                    duration -= max(0, et - st)
                    
            total += max(0, duration)
        return int(total)


class PlaylistItem(Base):
    __tablename__ = "playlist_items"

    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    media_id = Column(Integer, ForeignKey("media_item.id"))
    position = Column(Integer, default=0)
    role = Column(String, default="CONTENT")  # "OPENING", "CONTENT", "CLOSING"
