# Base de Menus da TUI

import os
import time
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm

console = Console()

class BaseMenu:
    label = "Menu Base"
    order = 99
    
    def __init__(self, db, scanner, service, page_size):
        self.db = db
        self.scanner = scanner
        self.service = service
        self.page_size = page_size

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def execute(self):
        raise NotImplementedError("O método execute deve ser implementado pela subclasse.")
