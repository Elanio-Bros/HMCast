import os
import time
import threading
import subprocess
import random
from datetime import datetime, timezone
from .database import SessionLocal
from .models import Channels, ChannelSchedule, Playlist, PlaylistItem, MediaItem
from .player import Player
from .media_utils import MediaUtils


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
        self.last_access = 0.0 # 0.0 significa que ainda não houve acesso real (warmup)
        self.start_time = time.time() 
        self.current_schedule_id = None
        self.running = False
        self._cleanup_lock = threading.Lock()
        self._cleanup_running = False

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
            # Obtém modo do canal com segurança
            mode = getattr(self.channel, 'execution_mode', 'ON_DEMAND')
            
            # Se for ALWAYS_ON, nunca para por inatividade
            if mode == "ALWAYS_ON":
                time.sleep(10)
                continue
                
            # Tempo de inatividade
            if self.last_access > 0:
                idle_time = time.time() - self.last_access
            else:
                # V7: No warmup, o idle_time conta a partir do start_time para não matar imediatamente
                idle_time = time.time() - self.start_time
            
            # No modo PREDICTIVE, se não houver views, paramos mais rápido após o warmup (e.g. 30s)
            terminate_threshold = float(self.IDLE_TIMEOUT)
            if mode == "PREDICTIVE" and self.last_access == 0: # 0 indica que foi um warmup worker
                 terminate_threshold = float(os.getenv("PREDICTIVE_WARMUP_DURATION", "30"))

            if idle_time > terminate_threshold:
                print(f"[Channel {self.channel.id}] 💤 Inativo (Modo {mode}), encerrando")
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
                media.hms_to_seconds(finish["end"])
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
        """
        Retorna a lista de segmentos (start, duration) que devem ser tocados
        a partir do internal_offset.
        """
        acc = 0.0
        remaining = []
        
        found_start = False
        for i, (start, end) in enumerate(segments):
            seg_len = end - start
            
            if not found_start:
                if internal_offset < acc + seg_len:
                    # Este é o segmento onde o offset cai
                    offset_inside = internal_offset - acc
                    start_time = start + offset_inside
                    play_duration = end - start_time
                    remaining.append((start_time, play_duration))
                    found_start = True
                else:
                    acc += seg_len
            else:
                # Todos os segmentos subsequentes são incluídos integralmente
                remaining.append((start, seg_len))

        return remaining if remaining else None

    # ---------------- PLAYLIST / MEDIAS ----------------

    def get_active_schedule(self):
        #Busca o agendamento ativo respeitando a HIERARQUIA DE RELEVÂNCIA.
        now_local = datetime.now().astimezone()
        now_time = now_local.time()
        
        day_name = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][now_local.weekday()]
        month_day = now_local.day
        date_dm = now_local.strftime("%d/%m")
        date_dmy = now_local.strftime("%d/%m/%Y")

        with SessionLocal() as db:
            schedules = (
                db.query(ChannelSchedule)
                .filter(ChannelSchedule.channel_id == self.channel.id)
                .all()
            )

        # 1. Filtra apenas quem está na janela de horário
        candidates = []
        for sch in schedules:
            st, et = sch.start_time, sch.end_time
            in_window = (st <= now_time <= et) if st <= et else (now_time >= st or now_time <= et)
            if in_window:
                candidates.append(sch)

        if not candidates:
            return None

        # 2. Calcula "Score de Relevância" para cada candidato
        # Prioridade: DD/MM/YYYY (4) > DD/MM (3) > Dia do Mês (2) > Dia da Semana (1) > Todo dia (0)
        scored_candidates = []
        for sch in candidates:
            score = 0
            match = False
            
            # Checa Data Única (DD/MM/YYYY)
            if sch.specific_dates and date_dmy in sch.specific_dates:
                score = 4
                match = True
            # Checa Data Anual (DD/MM)
            elif sch.specific_dates and date_dm in sch.specific_dates:
                score = 3
                match = True
            # Checa Dia do Mês (DD)
            elif sch.month_days and month_day in sch.month_days:
                score = 2
                match = True
            # Checa Dia da Semana
            elif sch.weekdays and day_name in sch.weekdays:
                score = 1
                match = True
            # Regra "Todo dia" (sem filtros)
            elif not sch.weekdays and not sch.month_days and not sch.specific_dates:
                score = 0
                match = True
            
            if match:
                scored_candidates.append((score, sch))

        if not scored_candidates:
            return None

        # 3. Retorna o candidato com maior score (mais específico)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return scored_candidates[0][1]

    def resolve_playlist_items(self, playlist):
        with SessionLocal() as db:
            items = (
                db.query(PlaylistItem, MediaItem)
                .join(MediaItem, MediaItem.id == PlaylistItem.media_id)
                .filter(PlaylistItem.playlist_id == playlist.id)
                .order_by(PlaylistItem.position.asc())
                .all()
            )
            
            # Agrupar por papel
            openings = []
            contents = []
            closings = []
            
            for p_item, m_item in items:
                if p_item.role == "OPENING":
                    openings.append(m_item)
                elif p_item.role == "CLOSING":
                    closings.append(m_item)
                else:
                    contents.append(m_item)

            # Shuffle apenas o miolo (CONTEUDO)
            if playlist.shuffle and contents:
                seed = f"{datetime.now().date()}_{playlist.id}_{self.channel.id}"
                random.Random(seed).shuffle(contents)

            return openings + contents + closings

    def cleanup_old_segments(self):
        def worker():
            with self._cleanup_lock:
                if self._cleanup_running:
                    return
                self._cleanup_running = True
            
            try:
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
                    retention_str = os.getenv("CHANNEL_PLAYLIST_RETENTION_SEC", "600")
                    retention = int(retention_str)
                except Exception:
                    retention = 600
                now = time.time()

                for file in m3u8_files:
                    if file == "master.m3u8":
                        continue
                    path = os.path.join(self.channel_folder, file)
                    try:
                        m_time = os.path.getmtime(path)
                        # Se a playlist não é atualizada há muito tempo, remover
                        if now - m_time > retention:
                            os.remove(path)
                            print(f"[Channel {self.channel.id}] Removida playlist antiga: {file}")
                    except Exception as e:
                        print(f"[Channel {self.channel.id}] Erro ao tratar playlist {file}: {e}")

                # SAFETY VALVE: Limite rígido de arquivos .ts para evitar vazamento de disco
                try:
                    hard_limit_str = os.getenv("CHANNEL_SEGMENT_HARD_LIMIT", "50")
                    hard_limit = int(hard_limit_str)
                    all_ts = [
                        (os.path.join(self.channel_folder, f), os.path.getmtime(os.path.join(self.channel_folder, f)))
                        for f in os.listdir(self.channel_folder) if f.endswith(".ts")
                    ]
                    if len(all_ts) > hard_limit:
                        # Ordena pelos mais antigos
                        all_ts.sort(key=lambda x: x[1])
                        excess = len(all_ts) - hard_limit
                        print(f"[Channel {self.channel.id}] SAFETY VALVE: Removendo {excess} segmentos antigos excedentes.")
                        for path, _ in all_ts[:excess]:
                            try:
                                os.remove(path)
                            except Exception:
                                pass
                except Exception as e:
                    print(f"[Channel {self.channel.id}] Erro no Safety Valve: {e}")
            
            except Exception as e:
                print(f"[Channel {self.channel.id}] Erro crítico no worker de limpeza: {e}")
            finally:
                with self._cleanup_lock:
                    self._cleanup_running = False

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
                    # Auditoria V4: Verifica se o arquivo existe fisicamente
                    if not os.path.exists(media.file):
                        print(f"[Channel {self.channel.id}] ⚠️ ARQUIVO NÃO ENCONTRADO (PULANDO): {media.file}")
                        continue

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
                    acc_duration = float(acc_duration) + duration
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
                # Verificação de validade do agendamento (evita loop infinito na mesma playlist)
                now_curr = datetime.now().astimezone().time()
                st_curr = schedule.start_time
                et_curr = schedule.end_time
                
                is_overnight = st_curr > et_curr
                if is_overnight:
                    in_window = (now_curr >= st_curr) or (now_curr <= et_curr)
                else:
                    in_window = (st_curr <= now_curr <= et_curr)
                
                if not in_window:
                    print(f"[Channel {self.channel.id}] Agendamento expirou ({et_curr}), recarregando...")
                    break

                slot = timeline[idx]
                ep = slot["media"]

                remaining_segments = self.resolve_offset(
                    slot["segments"],
                    internal_offset
                )

                # Se cálculo falhou ou lista vazia, pula item
                if not remaining_segments:
                    print(f"[Channel {self.channel.id}] Slot inválido; pulando item: {ep.name}")
                    idx = int((idx + 1) % len(timeline))
                    internal_offset = 0
                    time.sleep(0.5)
                    continue

                print(f"[Channel {self.channel.id}] Iniciando: {ep.name}")
                # print(f"Segmentos: {remaining_segments}")
                self.player.start(
                    ep.file,
                    self.channel_folder,
                    remaining_segments,
                    channel_type=getattr(self.channel, 'type', 'TV')
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
                    current_retry = int(self.retry_counts.get(media_key, 0)) + 1
                    if current_retry <= self.MAX_RETRIES:
                        self.retry_counts[media_key] = current_retry
                        print(f"[Channel {self.channel.id}] FFmpeg falhou ao iniciar; retry {current_retry}/{self.MAX_RETRIES} em {self.RETRY_DELAY}s")
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
                
                # MONITOR DE HANG: Loop de espera com check de progresso
                last_log_size = 0
                hang_counter = 0
                max_hang = 12  # 12 * 5s = 60s sem resposta = kill
                
                log_path = os.path.join(self.channel_folder, "ffmpeg.log")
                
                while not self.stop_signal and self.player.process.poll() is None:
                    try:
                        self.player.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Verifica se o log está crescendo
                        if os.path.exists(log_path):
                            current_size = os.path.getsize(log_path)
                            if current_size > last_log_size:
                                last_log_size = current_size
                                hang_counter = 0
                            else:
                                hang_counter += 1
                        else:
                            hang_counter += 1
                        
                        if hang_counter >= max_hang:
                            print(f"[Channel {self.channel.id}] FFmpeg parou de responder (hang); reiniciando...")
                            self.player.stop()
                            break
                    except Exception:
                        break

                # Limpeza final de descritores neste ciclo
                try:
                    if self.player.err_fd:
                        self.player.err_fd.close()
                except Exception:
                    pass
                finally:
                    self.player.err_fd = None

                print(
                    f"[Channel {self.channel.id}] Episódio finalizado: {ep.name}")
                # Garante reset do contador ao concluir com sucesso
                self.retry_counts.pop(media_key, None)
                self.cleanup_old_segments()

                # Próximo episódio
                idx = (idx + 1) % len(timeline)
                internal_offset = 0
