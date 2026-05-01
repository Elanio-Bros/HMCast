from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, SelectionList, Label, Input, ContentSwitcher, Tree, ProgressBar
from textual.widgets.tree import TreeNode
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal
from app.database import SessionLocal
from app.models import MediaItem, MediaFolder
import os

class FolderTree(Tree):
    """Uma árvore customizada que lista APENAS pastas, de forma garantida."""
    def __init__(self, label: str, path: str, **kwargs):
        super().__init__(label, **kwargs)
        self.root_path = path

    def on_mount(self) -> None:
        self.root.data = self.root_path
        self.load_directory(self.root)
        self.root.expand()

    def load_directory(self, node: TreeNode) -> None:
        """Lê o diretório e adiciona apenas as subpastas como nós."""
        path = node.data
        if not path or not os.path.isdir(path):
            return
        
        node.remove_children()
        
        try:
            with os.scandir(path) as it:
                for entry in sorted(it, key=lambda e: e.name.lower()):
                    if entry.is_dir():
                        child_node = node.add(entry.name, data=entry.path)
                        child_node.allow_expand = True
        except PermissionError:
            pass

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        node = event.node
        if not node.children:
            self.load_directory(node)

    @property
    def path(self) -> str:
        return self.root_path

    @path.setter
    def path(self, value: str) -> None:
        self.root_path = value
        self.root.label = os.path.basename(value) or value
        self.root.data = value
        self.root.remove_children()
        self.load_directory(self.root)
        self.root.expand()

class AddMediaModal(ModalScreen[bool]):
    """Modal unificado para adicionar mídias (Pasta Inteira ou Seleção Manual)."""

    def __init__(self, media_view=None, **kwargs):
        super().__init__(**kwargs)
        self.media_view = media_view

    def compose(self) -> ComposeResult:
        with Vertical(id="scan-container"):
            yield Static("ADICIONAR MÍDIAS", id="scan-title")
            
            with ContentSwitcher(initial="step-select-folder", id="add-switcher"):
                # Passo 1: Selecionar Pasta
                with Vertical(id="step-select-folder"):
                    yield Label("Selecione a PASTA de origem:")
                    yield Input(value=".", placeholder="Ex: D:/Videos", id="input-path")
                    yield FolderTree("PROJETO", ".", id="dir-tree")
                    yield ProgressBar(id="modal-scan-progress", show_percentage=True)
                    with Horizontal(classes="scan-footer"):
                        yield Button("Finalizar", variant="error", id="btn-finish-all")
                        yield Button("Importar Pasta (Auto-Scan)", variant="success", id="btn-import-folder")
                        yield Button("Selecionar Arquivos", variant="primary", id="btn-list-files")
                
                # Passo 2: Selecionar Arquivos
                with Vertical(id="step-select-files"):
                    yield Label("Marque os arquivos que deseja importar (MANUAL):")
                    yield SelectionList(id="selection-list")
                    with Horizontal(classes="scan-footer"):
                        yield Button("Voltar", id="btn-back")
                        yield Button("Marcar Todos", id="btn-select-all")
                        yield Button("Desmarcar Todos", id="btn-deselect-all")
                        yield Button("Importar Selecionados", variant="success", id="btn-confirm-import")

    def on_mount(self) -> None:
        self.query_one("#modal-scan-progress").display = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-path":
            if os.path.exists(event.value):
                self.query_one("#dir-tree", FolderTree).path = event.value

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        self.selected_path = str(event.node.data)
        self.query_one("#input-path", Input).value = self.selected_path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        path = getattr(self, "selected_path", None) or self.query_one("#input-path").value
        
        if event.button.id == "btn-finish-all":
            self.dismiss(None)
        elif event.button.id == "btn-import-folder":
            if os.path.exists(path):
                m_progress = self.query_one("#modal-scan-progress", ProgressBar)
                m_progress.display = True
                m_progress.progress = 0
                
                try:
                    if self.media_view:
                        self.media_view.start_folder_scan(path, m_progress=m_progress)
                except Exception as e:
                    self.app.notify(f"Erro ao iniciar scan: {e}", severity="error")

        elif event.button.id == "btn-list-files":
            if os.path.exists(path):
                self.show_files_for_selection(path)
        elif event.button.id == "btn-back":
            self.query_one("#add-switcher").current = "step-select-folder"
        elif event.button.id == "btn-select-all":
            self.query_one("#selection-list", SelectionList).select_all()
        elif event.button.id == "btn-deselect-all":
            self.query_one("#selection-list", SelectionList).deselect_all()
        elif event.button.id == "btn-confirm-import":
            self.run_import_worker()

    def show_files_for_selection(self, path: str) -> None:
        switcher = self.query_one("#add-switcher")
        selection_list = self.query_one("#selection-list", SelectionList)
        selection_list.clear_options()
        
        all_files = list(self.app.scanner.iter_media_files(path))
        if not all_files:
            self.app.notify("Nenhum arquivo encontrado!", severity="warning")
            return

        with SessionLocal() as db:
            existing_paths = {row[0] for row in db.query(MediaItem.file).all()}
            options = [Selection(os.path.basename(f), f) for f in all_files if f not in existing_paths]
            
            if not options:
                self.app.notify("Arquivos já cadastrados.", severity="information")
                return
            
            selection_list.add_options(options)
            switcher.current = "step-select-files"

    def run_import_worker(self) -> None:
        selected_files = self.query_one("#selection-list", SelectionList).selected
        if not selected_files:
            self.app.notify("Selecione ao menos um arquivo!", severity="error")
            return
            
        m_progress = self.query_one("#modal-scan-progress", ProgressBar)
        m_progress.display = True
        m_progress.progress = 0
        
        try:
            if self.media_view:
                self.media_view.start_manual_import(selected_files, m_progress=m_progress)
            self.query_one("#add-switcher").current = "step-select-folder"
        except Exception as e:
            self.app.notify(f"Erro ao iniciar importação manual: {e}", severity="error")
