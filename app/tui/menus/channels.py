import time
from rich.table import Table
from rich import box
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, Confirm
from app.models import Channels
from app.tui.base import BaseMenu, console

class ChannelsMenu(BaseMenu):
    label = "📡 Gerenciar Canais"
    order = 1

    def execute(self):
        page = 0
        while True:
            self.clear_screen()
            total = self.db.query(Channels).count()
            total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
            
            offset = page * self.page_size
            channels = self.db.query(Channels).offset(offset).limit(self.page_size).all()
            
            table = Table(title=f"CANAIS CONFIGURADOS (Pág {page+1} de {total_pages})", box=box.ROUNDED, header_style="bold cyan")
            table.add_column("ID", justify="center")
            table.add_column("NOME", style="bold")
            table.add_column("TIPO", justify="center")
            table.add_column("MODO", justify="center")

            for c in channels:
                style = "green" if c.execution_mode == "ALWAYS_ON" else "blue"
                table.add_row(str(c.id), c.name, c.type, Text(c.execution_mode, style=style))
            
            console.print(table)
            console.print(f"\n[bold cyan][N][/] Próxima | [bold cyan][P][/] Anterior | [bold cyan][G][/] Ir para Pág | [bold cyan][A][/] Adicionar | [bold yellow][E][/] Editar | [bold red][D][/] Deletar | [bold white][V][/] Voltar")
            
            choices = ["n", "p", "g", "a", "e", "d", "v"]
            opt = Prompt.ask("Opção", choices=choices, default="v").lower()
            
            if opt == "v": break
            if opt == "n": page = (page + 1) % total_pages
            if opt == "p": page = (page - 1) % total_pages
            if opt == "g":
                target = IntPrompt.ask(f"Ir para página (1-{total_pages})", default=page+1)
                if 1 <= target <= total_pages: page = target - 1
            
            if opt == "a": self.add_channel()
            elif opt == "e": self.edit_channel()
            elif opt == "d": self.delete_channel()

    def add_channel(self):
        name = Prompt.ask("Nome do Canal")
        ctype = Prompt.ask("Tipo", choices=["TV", "RADIO"], default="TV")
        mode = Prompt.ask("Modo de Execução", choices=["ALWAYS_ON", "ON_DEMAND", "PREDICTIVE"], default="ON_DEMAND")
        
        new_ch = Channels(name=name, type=ctype, execution_mode=mode)
        self.db.add(new_ch)
        self.db.commit()
        console.print("[bold green]✔ Canal criado com sucesso![/]")
        time.sleep(1)

    def delete_channel(self):
        cid = IntPrompt.ask("ID do Canal para deletar")
        ch = self.db.get(Channels, cid)
        if ch and Confirm.ask(f"Tem certeza que deseja deletar o canal '{ch.name}'?"):
            self.db.delete(ch)
            self.db.commit()
            console.print("[bold red]✘ Canal removido.[/]")
            time.sleep(1)

    def edit_channel(self):
        cid = IntPrompt.ask("ID do Canal para editar")
        ch = self.db.get(Channels, cid)
        if ch:
            ch.name = Prompt.ask("Novo Nome", default=ch.name)
            ch.type = Prompt.ask("Novo Tipo", choices=["TV", "RADIO"], default=ch.type)
            ch.execution_mode = Prompt.ask("Novo Modo", choices=["ALWAYS_ON", "ON_DEMAND", "PREDICTIVE"], default=ch.execution_mode)
            self.db.commit()
            console.print("[bold green]✔ Canal atualizado![/]")
            time.sleep(1)
