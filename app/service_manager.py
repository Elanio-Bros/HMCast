import os
import subprocess
import signal
import time
import sys
import psutil

class ServiceManager:
    def __init__(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.pid_file = os.path.join(self.root_dir, "data", "server.pid")
        self.log_file = os.path.join(self.root_dir, "data", "logs", "server.log")
        self.error_log = os.path.join(self.root_dir, "data", "logs", "error.log")

    def is_running(self):
        """Verifica se o processo está rodando baseado no arquivo PID"""
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                # Verifica se o processo é realmente um uvicorn/python relacionado
                process = psutil.Process(pid)
                return any("python" in cmd.lower() or "uvicorn" in cmd.lower() for cmd in process.cmdline())
            return False
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def start_service(self):
        """Inicia o servidor em background"""
        if self.is_running():
            return False, "O serviço já está em execução."

        # Garante que a pasta de logs existe
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # Comando para iniciar o uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]

        # Configura o ambiente para forçar UTF-8 nos logs do subprocesso
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # Abre os arquivos de log
        out_log = open(self.log_file, "a", encoding="utf-8")

        # Configurações de criação de processo (Windows vs Linux)
        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=out_log,
                stderr=out_log,
                creationflags=creation_flags,
                close_fds=True if os.name != "nt" else False,
                env=env
            )

            # Salva o PID
            with open(self.pid_file, "w") as f:
                f.write(str(process.pid))
            
            return True, f"Serviço iniciado com PID {process.pid}"
        except Exception as e:
            return False, f"Erro ao iniciar serviço: {str(e)}"

    def stop_service(self):
        """Para o serviço enviando sinal de encerramento"""
        if not os.path.exists(self.pid_file):
            return False, "Arquivo PID não encontrado. O serviço está rodando?"

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                # No Windows, kill recursivo para garantir que o uvicorn pare os workers
                for child in process.children(recursive=True):
                    child.terminate()
                process.terminate()
                
                # Espera o processo morrer
                gone, alive = psutil.wait_procs([process], timeout=5)
                if alive:
                    for p in alive: p.kill()
                
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                
            return True, "Serviço encerrado com sucesso."
        except Exception as e:
            return False, f"Erro ao parar o serviço: {str(e)}"

    def get_status(self):
        if self.is_running():
            with open(self.pid_file, "r") as f:
                pid = f.read().strip()
            return f"RODANDO (PID {pid})"
        return "PARADO"

    def get_logs(self, lines=20):
        if not os.path.exists(self.log_file):
            return "Nenhum log encontrado."
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.readlines()
                return "".join(content[-lines:])
        except Exception as e:
            return f"Erro ao ler logs: {str(e)}"
