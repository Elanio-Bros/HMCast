import os
import time
import threading
import subprocess
import random
from datetime import datetime, timezone, timedelta
from .database import SessionLocal
from .models import Channels, ChannelSchedule, Playlist, PlaylistItem, MediaItem
from .enums import PlaylistItemRole
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

    def build_segments(self, media, role: PlaylistItemRole, is_first: bool, is_last: bool):
        # Obtém os tempos de corte baseados no papel (role)
        start, end = media.get_cut_times(role, is_first, is_last)
        skips = media.skips or {}
        forbidden = []

        # --- CUTS (Sempre proibidos) ---
        for cut in skips.get("cuts", []):
            c_start = media.hms_to_seconds(cut["start"])
            c_end = media.hms_to_seconds(cut["end"])
            # Só considera cortes que estão dentro do intervalo visível (entre start e end)
            actual_cut_start = max(start, c_start)
            actual_cut_end = min(end, c_end)
            if actual_cut_end > actual_cut_start:
                forbidden.append((actual_cut_start, actual_cut_end))

        # Ordena tudo para construir os segmentos válidos
        forbidden.sort()

        # Agora constrói os segmentos válidos dentro da janela [start, end]
        segments = []
        cursor = start

        for f_start, f_end in forbidden:
            if cursor < f_start:
                segments.append((cursor, f_start))
            cursor = max(cursor, f_end)

        if cursor < end:
            segments.append((cursor, end))

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
        """
        Retorna o agendamento que deve estar no ar AGORA ou o próximo de HOJE.
        """
        from datetime import timedelta
        now_local = datetime.now().astimezone()
        today = now_local.date()

        with SessionLocal() as db:
            schedules = (
                db.query(ChannelSchedule)
                .filter(ChannelSchedule.channel_id == self.channel.id)
                .all()
            )

        def get_actual_start_end(sch, base_date):
            st = datetime.combine(base_date, sch.start_time).replace(tzinfo=now_local.tzinfo)
            et = datetime.combine(base_date, sch.end_time).replace(tzinfo=now_local.tzinfo)
            if sch.start_time > sch.end_time: # Overnight
                et += timedelta(days=1)
            return st, et

        def match_criteria(sch, dt):
            day_name = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][dt.weekday()]
            month_day = dt.day
            date_dm = dt.strftime("%d/%m")
            date_dmy = dt.strftime("%d/%m/%Y")
            
            if sch.specific_dates and date_dmy in sch.specific_dates: return 4
            if sch.specific_dates and date_dm in sch.specific_dates: return 3
            if sch.month_days and month_day in sch.month_days: return 2
            if sch.weekdays and day_name in sch.weekdays: return 1
            if not sch.weekdays and not sch.month_days and not sch.specific_dates: return 0
            return -1

        active_candidates = []
        future_today_candidates = []

        yesterday = today - timedelta(days=1)

        for sch in schedules:
            # 1. Checa Ontem (para casos de virada de dia/overnight) e Hoje
            for base_d in [yesterday, today]:
                st_dt, et_dt = get_actual_start_end(sch, base_d)
                score = match_criteria(sch, base_d)
                
                if score >= 0:
                    # Caso A: Estamos dentro da janela (Ativo)
                    if st_dt <= now_local <= et_dt:
                        active_candidates.append((score, sch, st_dt))
                    # Caso B: É um agendamento de HOJE que ainda vai acontecer
                    elif now_local < st_dt and base_d == today:
                        future_today_candidates.append((st_dt, sch))

        # Se temos algo ativo agora, prioridade total (melhor score)
        if active_candidates:
            active_candidates.sort(key=lambda x: x[0], reverse=True)
            best = active_candidates[0]
            return best[1], best[2]

        # Se não tem nada ativo, mas tem algo para HOJE ainda, pegamos o primeiro (mais próximo)
        if future_today_candidates:
            future_today_candidates.sort(key=lambda x: x[0]) # Ordena pelo horário de início
            next_sch = future_today_candidates[0]
            print(f"[Channel {self.channel.id}] ⏩ Antecipando agendamento de hoje: {next_sch[1].start_time}")
            return next_sch[1], next_sch[0]

        return None, None

    def resolve_playlist_items(self, playlist):
        with SessionLocal() as db:
            items = (
                db.query(PlaylistItem, MediaItem)
                .join(MediaItem, MediaItem.id == PlaylistItem.media_id)
                .filter(PlaylistItem.playlist_id == playlist.id)
                .order_by(PlaylistItem.position.asc())
                .all()
            )
            
            openings = []
            contents = []
            closings = []
            
            for p_item, m_item in items:
                # Converte string para Enum
                try: role_enum = PlaylistItemRole(p_item.role)
                except: role_enum = PlaylistItemRole.AUTO
                
                data = {"media": m_item, "role": role_enum, "playlist_item_id": p_item.id}
                
                if role_enum == PlaylistItemRole.OPENING:
                    openings.append(data)
                elif role_enum == PlaylistItemRole.CLOSING:
                    closings.append(data)
                else:
                    contents.append(data)

            # Shuffle apenas o miolo (CONTEUDO)
            if playlist.shuffle and contents:
                seed = f"{datetime.now().date()}_{playlist.id}_{self.channel.id}"
                random.Random(seed).shuffle(contents)

            return openings, contents, closings

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
            schedule, st_dt = self.get_active_schedule()
            if not schedule:
                time.sleep(5)
                continue
                
            # Calcula o end_dt
            end_dt = datetime.combine(st_dt.date(), schedule.end_time).replace(tzinfo=st_dt.tzinfo)
            if schedule.start_time > schedule.end_time:
                end_dt += timedelta(days=1)

            with SessionLocal() as db:
                playlist = db.get(Playlist, schedule.playlist_id)
            if not playlist:
                time.sleep(5)
                continue

            openings, contents, closings = self.resolve_playlist_items(playlist)
            if not (openings or contents or closings):
                time.sleep(5)
                continue
                
            # Monta a Timeline da Sessão
            session_items = []
            for item in openings: session_items.append(item)
            
            # Conteúdo Sequencial (com memória)
            if contents:
                idx_saved = schedule.current_item_index % len(contents)
                rotated_contents = contents[idx_saved:] + contents[:idx_saved]
                for item in rotated_contents: session_items.append(item)
                
            for item in closings: session_items.append(item)

            # Constrói a timeline física (com segmentos e cuts)
            timeline = []
            for i, item in enumerate(session_items):
                media = item["media"]
                role = item["role"]
                
                # Regra AUTO: Primeiro conteúdo da sessão é HEAD, último é TAIL
                # Mas aqui, como temos openings/closings fixos, os conteúdos são intermediários
                is_first = (i == 0)
                is_last = (i == len(session_items) - 1)
                
                # Se houver openings, o primeiro conteúdo NÃO é o primeiro da sessão
                # Então o build_segments cuidará disso via get_cut_times
                
                segments = self.build_segments(media, role, is_first, is_last)
                duration = self.effective_duration(segments)
                if duration > 0:
                    timeline.append({
                        "media": media,
                        "playlist_item_id": item["playlist_item_id"],
                        "segments": segments,
                        "duration": duration,
                        "role": role
                    })

            if not timeline:
                time.sleep(5); continue

            idx = 0
            internal_offset = 0
            
            # Clock Sync inicial (Opcional, pode ser desativado para sempre começar do início)
            now = datetime.now().astimezone()
            if now > st_dt + timedelta(seconds=30):
                # Se você quiser que o canal SEMPRE comece do início (Maratona pura), 
                # basta ignorar o cálculo de offset inicial.
                pass

            while not self.stop_signal:
                # Verificação de validade do agendamento
                current_sch, current_st = self.get_active_schedule()
                if not current_sch or current_sch.id != schedule.id or current_st != st_dt:
                    break

                slot = timeline[idx]
                media = slot["media"]
                role = slot["role"]
                
                # --- INTELIGÊNCIA DE TRANSIÇÃO FLEXÍVEL (CASCATA) ---
                now = datetime.now().astimezone()
                
                # Se o horário já estourou...
                if now >= end_dt:
                    # ...e ainda não estamos nos encerramentos, pulamos para eles
                    if role not in [PlaylistItemRole.OPENING, PlaylistItemRole.CLOSING]:
                        found_closing = False
                        for i, t in enumerate(timeline):
                            if t["role"] == PlaylistItemRole.CLOSING:
                                idx = i; found_closing = True; break
                        
                        if found_closing:
                            slot = timeline[idx]
                            media = slot["media"]
                            role = slot["role"]
                        else:
                            # Se não tem encerramento fixo e o tempo acabou, encerra o bloco
                            break

                # --- DECISÃO DE IS_LAST (Para regra AUTO) ---
                is_last_item = (idx == len(timeline) - 1)
                if not is_last_item and role not in [PlaylistItemRole.OPENING, PlaylistItemRole.CLOSING]:
                    # Se este item terminar depois do horário de fim, ele é o "último" desta sessão
                    if (now + timedelta(seconds=slot["duration"])) > end_dt:
                        is_last_item = True
                    else:
                        # Ou se o próximo item for um CLOSING
                        if timeline[idx+1]["role"] == PlaylistItemRole.CLOSING:
                            is_last_item = True

                # Recalcula segmentos se o status de is_last_item mudou
                is_first_item = (idx == 0)
                segments = self.build_segments(media, role, is_first_item, is_last_item)
                
                remaining = self.resolve_offset(segments, internal_offset)
                if not remaining:
                    idx = (idx + 1) % len(timeline); internal_offset = 0
                    continue

                print(f"[Channel {self.channel.id}] Iniciando [{role.value}]: {media.name} (Last={is_last_item})")
                
                # Passa a lista de segmentos diretamente, pois 'remaining' já é uma lista de tuplas (start, duration)
                standard_segments = remaining

                self.player.start(media.file, self.channel_folder, standard_segments, channel_type=getattr(self.channel, 'type', 'TV'))
                
                # Monitor
                log_path = os.path.join(self.channel_folder, "ffmpeg.log")
                last_log_size = 0
                hang_counter = 0
                
                while not self.stop_signal and self.player.process and self.player.process.poll() is None:
                    try:
                        self.player.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        if os.path.exists(log_path):
                            curr_size = os.path.getsize(log_path)
                            if curr_size > last_log_size:
                                last_log_size = curr_size
                                hang_counter = 0
                            else:
                                hang_counter += 1
                        else: hang_counter += 1
                        
                        if hang_counter >= 12: self.player.stop(); break
                    except: break

                # Salva Progresso se for CONTENT
                if slot["role"] not in [PlaylistItemRole.OPENING, PlaylistItemRole.CLOSING]:
                    try:
                        orig_idx = -1
                        for i, c in enumerate(contents):
                            if c["playlist_item_id"] == slot["playlist_item_id"]:
                                orig_idx = i; break
                        
                        if orig_idx != -1:
                            next_idx = (orig_idx + 1) % len(contents)
                            with SessionLocal() as db_sync:
                                sch_db = db_sync.get(ChannelSchedule, schedule.id)
                                if sch_db:
                                    sch_db.current_item_index = next_idx
                                    db_sync.commit()
                    except: pass

                idx = (idx + 1) % len(timeline)
                internal_offset = 0
                
                if idx == 0: break

            self.cleanup_old_segments()
