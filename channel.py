import os
import time
import threading
from datetime import datetime, timezone
from database import SessionLocal
from models import Channels, ChannelSchedule, Playlist, PlaylistItem, MediaItem
from player import Player


class ChannelRuntime:
    IDLE_TIMEOUT = int(os.getenv("CHANNEL_IDLE_TIMEOUT", "60"))
    MAX_RETRIES = int(os.getenv("CHANNEL_MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("CHANNEL_RETRY_DELAY", "3"))

    def __init__(self, channel, hls_base_folder="hls_channels"):
        self.channel = channel
        self.player = Player()
        self.retry_counts = {}

        self.hls_base_folder = hls_base_folder
        self.channel_folder = f"{hls_base_folder}/channel_{channel.id}"

        self.thread = None
        self.stop_signal = False
        self.last_access = time.time()
        self.running = False

    def touch(self):
        """Atualiza última atividade"""
        self.last_access = time.time()

    # -------------------------------------------------

    def start(self):
        if self.running:
            return

        self.stop_signal = False
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

        self.running = True
        print(f"[Channel {self.channel.id}] ▶ Iniciado")

        # watchdog
        threading.Thread(target=self._watchdog, daemon=True).start()

    # -------------------------------------------------

    def stop(self):
        if not self.running:
            return

        print(f"[Channel {self.channel.id}] ⛔ Encerrando")

        self.stop_signal = True
        self.player.stop()
        self.running = False

        # Limpeza agressiva opcional no encerramento
        if os.getenv("CHANNEL_AGGRESSIVE_CLEANUP", "0") == "1":
            try:
                for f in os.listdir(self.channel_folder):
                    # Mantém logs a menos que explicitamente pedido para remover
                    if f.endswith(".log") and os.getenv("CHANNEL_KEEP_LOGS", "1") == "1":
                        continue
                    try:
                        os.remove(os.path.join(self.channel_folder, f))
                    except Exception:
                        pass
            except Exception:
                pass

    # -------------------------------------------------

    def _watchdog(self):
        try:
            interval = float(os.getenv("CHANNEL_WATCHDOG_INTERVAL", "2"))
        except Exception:
            interval = 2.0
        while self.running:
            if time.time() - self.last_access > self.IDLE_TIMEOUT:
                print(f"[Channel {self.channel.id}] 💤 Inativo, encerrando")
                self.stop()
                return
            time.sleep(max(interval, 0.5))

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
                (duration if finish['end'] ==
                 '-00:00:00' else media.hms_to_seconds(finish["end"]))
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

        with SessionLocal() as db:
            schedules = (
                db.query(ChannelSchedule)
                .filter(ChannelSchedule.channel_id == self.channel.id)
                .all()
            )

        for sch in schedules:
            st = sch.start_time
            et = sch.end_time
            # Intervalo padrão (mesmo dia)
            in_window = (st <= now_time <= et)
            # Intervalo overnight (cruza meia-noite): ex. 22:00 -> 02:00
            if st > et:
                in_window = (now_time >= st) or (now_time <= et)

            if not in_window:
                continue
            if sch.weekdays and weekday not in sch.weekdays:
                continue
            if sch.month_days and month_day not in sch.month_days:
                continue
            return sch
        return None

    def resolve_playlist_items(self, playlist):
        with SessionLocal() as db:
            items = (
                db.query(PlaylistItem, MediaItem)
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

            # Coleta segmentos referenciados por qualquer playlist .m3u8
            ts_files = [f for f in os.listdir(self.channel_folder) if f.endswith(".ts")]
            referenced_ts = set()
            m3u8_files = [f for f in os.listdir(self.channel_folder) if f.endswith(".m3u8")]

            for file in m3u8_files:
                try:
                    with open(os.path.join(self.channel_folder, file), "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.endswith(".ts"):
                                referenced_ts.add(line)
                except Exception as e:
                    print(f"[Channel {self.channel.id}] Erro ao ler {file}: {e}")

            # Remove segmentos .ts que não estão mais referenciados
            for ts in ts_files:
                if ts not in referenced_ts:
                    try:
                        os.remove(os.path.join(self.channel_folder, ts))
                        print(f"[Channel {self.channel.id}] Removido segmento antigo: {ts}")
                    except Exception as e:
                        print(f"[Channel {self.channel.id}] Erro ao remover {ts}: {e}")

            # Limpeza de playlists variantes muito antigas (não remove master.m3u8)
            try:
                retention = int(os.getenv("CHANNEL_PLAYLIST_RETENTION_SEC", "600"))  # 10 min padrão
            except Exception:
                retention = 600
            now = time.time()

            for file in m3u8_files:
                if file == "master.m3u8":
                    continue
                path = os.path.join(self.channel_folder, file)
                try:
                    mtime = os.path.getmtime(path)
                    # Se a playlist não é atualizada há muito tempo, remover
                    if now - mtime > retention:
                        os.remove(path)
                        print(f"[Channel {self.channel.id}] Removida playlist antiga: {file}")
                except Exception as e:
                    print(f"[Channel {self.channel.id}] Erro ao tratar playlist {file}: {e}")

        threading.Thread(target=worker, daemon=True).start()
    # ---------------- MAIN RUN ----------------

    def run(self):
        while not self.stop_signal:
            schedule = self.get_active_schedule()
            if not schedule:
                time.sleep(5)
                continue

            with SessionLocal() as db:
                playlist = db.get(Playlist, schedule.playlist_id)
            if not playlist:
                time.sleep(5)
                continue

            items = self.resolve_playlist_items(playlist)
            if not items:
                time.sleep(5)
                continue
            # Calcula offset com base na criação do canal (persistência)
            now = datetime.now(timezone.utc)
            channel_offset = int(
                (now - self.channel.created_at).total_seconds())
            acc_duration = 0
            timeline = []

            for i, media in enumerate(items):
                try:
                    is_first = i == 0
                    is_last = i == len(items) - 1
                    segments = self.build_segments(media, is_first, is_last)
                    duration = self.effective_duration(segments)
                    if duration <= 0:
                        # ignora itens efetivamente vazios
                        continue
                    timeline.append({
                        "media": media,
                        "segments": segments,
                        "duration": duration,
                    })
                    acc_duration += duration
                except Exception as e:
                    print(f"[Channel {self.channel.id}] Erro ao montar segmentos para '{getattr(media, 'name', 'media')}', pulando: {e}")
                    continue

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

                # Se cálculo falhou ou duração inválida, pula item
                if start_time is None or play_duration is None or play_duration <= 0:
                    print(f"[Channel {self.channel.id}] Slot inválido; pulando item: {ep.name}")
                    idx = (idx + 1) % len(timeline)
                    internal_offset = 0
                    time.sleep(0.5)
                    continue

                print(f"[Channel {self.channel.id}] Iniciando: {ep.name}")
                print(f"Start: {start_time}s | Duration: {play_duration}s")
                self.player.start(
                    ep.file,
                    self.channel_folder,
                    start_time,
                    play_duration
                )

                media_key = getattr(ep, 'id', ep.file)
                if not self.player.process:
                    # Falha ao iniciar FFmpeg
                    if not os.path.exists(ep.file):
                        # Falha permanente: arquivo não existe
                        print(f"[Channel {self.channel.id}] Arquivo inexistente, pulando permanente: {ep.file}")
                        # Zera contador (se houver)
                        self.retry_counts.pop(media_key, None)
                        # Avança para o próximo item
                        idx = (idx + 1) % len(timeline)
                        internal_offset = 0
                        time.sleep(0.5)
                        continue

                    # Falha transitória: aplicar retries
                    retry = self.retry_counts.get(media_key, 0) + 1
                    if retry <= self.MAX_RETRIES:
                        self.retry_counts[media_key] = retry
                        print(f"[Channel {self.channel.id}] FFmpeg falhou ao iniciar; retry {retry}/{self.MAX_RETRIES} em {self.RETRY_DELAY}s")
                        time.sleep(self.RETRY_DELAY)
                        # Tenta novamente a mesma mídia (sem avançar idx)
                        continue
                    else:
                        print(f"[Channel {self.channel.id}] Excedido retry para mídia; pulando item: {ep.name}")
                        self.retry_counts.pop(media_key, None)
                        idx = (idx + 1) % len(timeline)
                        internal_offset = 0
                        time.sleep(0.5)
                        continue

                # Iniciou com sucesso: zera contadores
                self.retry_counts.pop(media_key, None)
                self.player.process.wait()

                print(
                    f"[Channel {self.channel.id}] Episódio finalizado: {ep.name}")
                # Garante reset do contador ao concluir com sucesso
                self.retry_counts.pop(media_key, None)
                self.cleanup_old_segments()

                # Próximo episódio
                idx = (idx + 1) % len(timeline)
                internal_offset = 0
