import os
import subprocess
import time
import shutil
from media_utils import MediaUtils


class Player:
    def __init__(self):
        self.media = MediaUtils()
        self.process = None
        self.err_fd = None

    def start(self, input_file: str, output_dir: str, start_time: float = 0, duration: float = 0, channel_type: str = "TV"):
        # Encerrar qualquer processo anterior
        self.stop()
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"[Player] Falha ao criar diretório de saída '{output_dir}': {e}")
            return

        if not os.path.exists(input_file):
            print(f"[Player] Arquivo de entrada não existe: {input_file}")
            return

        # Verifica disponibilidade do FFmpeg
        ffmpeg_path = self.media.ffmpeg
        if not ((os.path.isabs(ffmpeg_path) and os.path.exists(ffmpeg_path)) or shutil.which(ffmpeg_path)):
            print(f"[Player] FFmpeg não encontrado: {ffmpeg_path}. Defina FFMPEG_BIN ou adicione ao PATH.")
            return

        # Log de erro por canal/saída
        ffmpeg_log = os.path.join(output_dir, "ffmpeg.log")
        try:
            self.err_fd = open(ffmpeg_log, "wb", buffering=0)
            err_dest = self.err_fd
        except Exception as e:
            print(f"[Player] Não foi possível abrir o log {ffmpeg_log}: {e}")
            self.err_fd = None
            err_dest = subprocess.DEVNULL

        # Imagem de fundo para rádio (opcional)
        bg_image = os.getenv("RADIO_BACKGROUND_IMAGE")
        # Se rádio mas sem imagem configurada, tentamos um fallback ou geramos cor sólida
        use_bg = (channel_type == "RADIO" and bg_image and os.path.exists(bg_image))

        # Monta comando base 
        cmd = [self.media.ffmpeg, "-re", "-y"]
        
        if use_bg:
            # Loop infinito da imagem
            cmd += ["-loop", "1", "-i", bg_image]
        
        cmd += [
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", input_file,
        ]

        # Se fallback de áudio silencioso estiver habilitado, adiciona segunda entrada lavfi anullsrc
        silence_fallback = os.getenv("AUDIO_SILENCE_FALLBACK", "0") == "1"
        if silence_fallback:
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]

        # Filtros e Mapeamento Adaptativo
        if channel_type == "RADIO":
            if use_bg:
                # Sobrepõe áudio na imagem, redimensionando a imagem para 1080p
                # -shortest faz o encode parar quando o áudio (input 1) acabar
                cmd += [
                    "-filter_complex",
                    "[0:v]scale=1920:1080,format=yuv420p[bg];" # Background
                    "[1:a]copy[aout]", # Audio
                    "-map", "[bg]", "-map", "[aout]",
                    "-shortest",
                    "-r", "2", # Baixo framerate para economizar CPU
                ]
            else:
                # Rádio sem imagem (Áudio Puro) -> Pouca compatibilidade, mas disponível
                cmd += [
                    "-vn", # No video
                    "-map", "0:a:0",
                ]
        else:
            # Modo TV (Original)
            cmd += [
                "-threads", "2",
                "-filter_complex",
                "[0:v]split=3[v1080][v720][v480];"
                "[v1080]scale=-2:1080[v1080out];"
                "[v720]scale=-2:720[v720out];"
                "[v480]scale=-2:480[v480out]",
                "-map", "[v1080out]", "-map", "0:a:0?",
                "-map", "[v720out]",  "-map", "0:a:0?",
                "-map", "[v480out]",  "-map", "0:a:0?",
            ]

        # Se fallback de silêncio estiver ativo, adiciona também mapa de áudio da segunda entrada (opcional)
        if silence_fallback:
            cmd += ["-map", "1:a:0?"]

        # Codecs e parâmetros
        cmd += [
            "-c:v", "libx264",
            "-preset", "ultrafast" if channel_type == "RADIO" else "veryfast",
            "-profile:v", "main",
            "-pix_fmt", "yuv420p",
            "-crf", "24" if channel_type == "RADIO" else "20",
            "-tune", "stillimage" if channel_type == "RADIO" else "zerolatency",
            "-g", os.getenv("HLS_GOP_SIZE", "50"),
            "-keyint_min", os.getenv("HLS_GOP_SIZE", "50"),
            "-c:a", "aac",
            "-ar", "44100" if channel_type == "RADIO" else "48000",
            "-ac", "2",
            "-b:a", "128k",
        ]
        
        if channel_type == "RADIO":
            # HLS simples para rádio
            cmd += [
                 "-f", "hls",
                 "-hls_time", "6",
                 "-hls_list_size", "10",
                 "-hls_flags", "delete_segments+append_list+omit_endlist",
                 "-hls_segment_filename", os.path.join(output_dir, "seg_%03d.ts"),
                 os.path.join(output_dir, "master.m3u8")
            ]
        else:
            # HLS Adaptativo para TV
            cmd += [
                "-b:v:0", "5000k", "-maxrate:v:0", "5350k", "-bufsize:v:0", "7500k",
                "-b:v:1", "2500k", "-maxrate:v:1", "2675k", "-bufsize:v:1", "3750k",
                "-b:v:2", "1000k", "-maxrate:v:2", "1070k", "-bufsize:v:2", "1500k",
                "-f", "hls",
                "-segment_list_flags", "+live+append_list",
                "-hls_time", "5",
                "-hls_list_size", "10",
                "-hls_delete_threshold", "5",
                "-hls_flags", "delete_segments+append_list+program_date_time+omit_endlist+discont_start",
                "-hls_allow_cache", "0",
                "-hls_segment_filename", os.path.join(output_dir, "v%v_seg_%03d.ts"),
                "-master_pl_name", "master.m3u8",
                "-var_stream_map", "v:0,a:0,name:1080p v:1,a:0,name:720p v:2,a:0,name:480p",
                os.path.join(output_dir, "v%v.m3u8")
            ]

        print(f"[Player] Iniciando FFmpeg para {input_file}...")
        
        popen_kwargs = {"stderr": err_dest}
        if os.name != 'nt':
            # Cria novo grupo de processos no Unix para permitir killpg
            popen_kwargs["start_new_session"] = True
            
        try:
            self.process = subprocess.Popen(cmd, **popen_kwargs)
        except Exception as e:
            print(f"[Player] Falha crítica ao iniciar FFmpeg: {e}")
            if self.err_fd:
                try:
                    self.err_fd.close()
                except:
                    pass
            self.err_fd = None
            self.process = None
            return
        # Checagem de falha rápida
        try:
            grace_ms = int(os.getenv("PLAYER_STARTUP_GRACE_MS", "1000"))
        except Exception:
            grace_ms = 1000
        time.sleep(max(grace_ms, 0) / 1000.0)
        if self.process.poll() is not None and self.process.returncode != 0:
            print(f"[Player] FFmpeg encerrou imediatamente com código {self.process.returncode}")
            try:
                if self.err_fd:
                    self.err_fd.flush()
                    self.err_fd.close()
            except Exception:
                pass
            self.err_fd = None
            self.process = None
            return
        print(f"[Player] FFmpeg iniciado: {input_file}")

    def stop(self):
        if self.process: # Verifica se existe objeto, independente de poll
            print("[Player] Encerrando FFmpeg...")
            
            # Tenta terminar graciosamente
            if self.process.poll() is None:
                try:
                    # No Windows, terminate() é o mesmo que kill() para subprocessos simples.
                    self.process.terminate()
                except Exception:
                    pass

            # Aguarda um pouco
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("[Player] Forçando kill no FFmpeg...")
                try:
                    # Se Unix e temos grupo de processos, mata o grupo todo
                    if os.name != 'nt':
                        import signal
                        try:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                        except Exception:
                            self.process.kill()
                    else:
                        self.process.kill()
                        
                    self.process.wait(timeout=2)
                except Exception:
                    pass
            
            # Garante que não hajam zumbis (Windows: taskkill / Unix: killpg safety)
            if self.process.poll() is None:
                if os.name == 'nt':
                     try:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], 
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                     except Exception:
                        pass
                else:
                    # Reforço para Unix
                    try:
                        import signal
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except Exception:
                        pass

        # Cleanup de arquivos descritores
        try:
            if self.err_fd:
                self.err_fd.close()
        except Exception:
            pass
        finally:
            self.err_fd = None
            self.process = None
