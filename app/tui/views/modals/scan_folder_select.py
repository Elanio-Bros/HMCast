from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, SelectionList, DirectoryTree, Label, Input
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal, ContentSwitcher
from app.database import SessionLocal
from app.models import MediaItem
import os

class ScanFolderSelectModal(ModalScreen[bool]):
    """Modal de Scan com Seleção Múltipla."""

    def compose(self) -> ComposeResult:
        with Vertical(id="scan-container"):
            yield Static("IMPORTAR NOVAS MÍDIAS", id="scan-title")
            
            with ContentSwitcher(initial="step-select-folder", id="scan-switcher"):
                # Passo 1: Selecionar Pasta
                with Vertical(id="step-select-folder"):
                    yield Label("Digite o caminho da pasta ou use a árvore:")
                    yield Input(value=".", placeholder="Ex: D:/Séries ou C:/Videos", id="input-scan-path")
                    yield DirectoryTree(".", id="scan-dir-tree")
                    with Horizontal(classes="scan-footer"):
                        yield Button("Cancelar", variant="error", id="btn-scan-cancel")
                        yield Button("Escanear Pasta", variant="primary", id="btn-do-scan")
                
                # Passo 2: Selecionar Arquivos
                with Vertical(id="step-select-files"):
                    yield Label("Marque os arquivos que deseja importar:")
                    yield SelectionList(id="scan-selection-list")
                    with Horizontal(classes="scan-footer"):
                        yield Button("Voltar", id="btn-scan-back")
                        yield Button("Marcar Todos", id="btn-scan-select-all")
                        yield Button("Desmarcar Todos", id="btn-scan-deselect-all")
                        yield Button("Importar Selecionados", variant="success", id="btn-confirm-scan-import")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.selected_path = str(event.path)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-scan-path":
            path = event.value
            if os.path.exists(path):
                tree = self.query_one("#scan-dir-tree", DirectoryTree)
                tree.path = path
            else:
                self.app.notify("Caminho inválido!", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-scan-cancel":
            self.dismiss(False)
            
        elif event.button.id == "btn-do-scan":
            path = getattr(self, "selected_path", None)
            if path and os.path.exists(path):
                self.show_files_for_selection(path)
            
        elif event.button.id == "btn-scan-back":
            self.query_one("#scan-switcher").current = "step-select-folder"
        elif event.button.id == "btn-scan-select-all":
            self.query_one("#scan-selection-list", SelectionList).select_all()
            self.app.notify("Todos os itens marcados!")
        elif event.button.id == "btn-scan-deselect-all":
            self.query_one("#scan-selection-list", SelectionList).deselect_all()
        elif event.button.id == "btn-confirm-scan-import":
            self.run_import()

    def show_files_for_selection(self, path: str) -> None:
        """Busca arquivos e preenche a SelectionList."""
        switcher = self.query_one("#scan-switcher")
        selection_list = self.query_one("#scan-selection-list", SelectionList)
        selection_list.clear_options()
        
        # Busca arquivos usando o MediaUtils do App
        all_files = list(self.app.scanner.iter_media_files(path))
        
        if not all_files:
            self.app.notify("Nenhum arquivo de mídia encontrado!", severity="warning")
            return

        with SessionLocal() as db:
            existing_paths = {row[0] for row in db.query(MediaItem.file).all()}
            
            new_options = []
            for f in all_files:
                if f not in existing_paths:
                    new_options.append(Selection(os.path.basename(f), f))
            
            if not new_options:
                self.app.notify("Todos os arquivos já estão cadastrados.", severity="information")
                return
            
            selection_list.add_options(new_options)
            switcher.current = "step-select-files"

    def run_import(self) -> None:
        """Executa a importação dos arquivos selecionados."""
        selected_files = self.query_one("#scan-selection-list", SelectionList).selected
        
        if not selected_files:
            self.app.notify("Selecione ao menos um arquivo!", severity="error")
            return

        import_count = 0
        with SessionLocal() as db:
            for f_path in selected_files:
                duration = self.app.scanner.get_media_duration(f_path)
                if duration > 0:
                    # Garante que a pasta exista (como auto_scan=True já que o user selecionou a pasta)
                    folder = self.app.scanner.get_or_create_folder(db, f_path, auto_scan=True)
                    
                    new_item = MediaItem(
                        name=os.path.splitext(os.path.basename(f_path))[0],
                        file=f_path,
                        duration=duration,
                        folder_id=folder.id
                    )
                    db.add(new_item)
                    import_count += 1
            db.commit()
            
        self.app.notify(f"Sucesso! {import_count} mídias importadas.", severity="success")
        self.dismiss(True)
