from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, SelectionList, Label, Input, ContentSwitcher, Tree
from textual.widgets.tree import TreeNode
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal
from app.database import SessionLocal
from app.models import MediaItem
import os
from pathlib import Path

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
            # Lista apenas diretórios
            with os.scandir(path) as it:
                for entry in sorted(it, key=lambda e: e.name.lower()):
                    if entry.is_dir():
                        child_node = node.add(entry.name, data=entry.path)
                        # Adiciona um nó falso para permitir expansão
                        child_node.allow_expand = True
        except PermissionError:
            pass

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Carrega o conteúdo da pasta ao expandir (Lazy Loading)."""
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

class AddMediaManualModal(ModalScreen[bool]):
    """Modal para adicionar mídias manuais com seletor de PASTAS real."""

    def compose(self) -> ComposeResult:
        with Vertical(id="scan-container"):
            yield Static("ADICIONAR MÍDIAS (MANUAL)", id="scan-title")
            
            with ContentSwitcher(initial="step-select-folder", id="manual-switcher"):
                # Passo 1: Selecionar Pasta
                with Vertical(id="step-select-folder"):
                    yield Label("Digite o caminho ou selecione a PASTA:")
                    yield Input(value=".", placeholder="Ex: D:/Videos", id="input-path")
                    yield FolderTree("PROJETO", ".", id="manual-dir-tree")
                    with Horizontal(classes="scan-footer"):
                        yield Button("Finalizar", variant="error", id="btn-finish-all")
                        yield Button("Listar Arquivos", variant="primary", id="btn-list-files")
                
                # Passo 2: Selecionar Arquivos
                with Vertical(id="step-select-files"):
                    yield Label("Marque os arquivos que deseja importar:")
                    yield SelectionList(id="manual-selection-list")
                    with Horizontal(classes="scan-footer"):
                        yield Button("Voltar", id="btn-back")
                        yield Button("Marcar Todos", id="btn-select-all")
                        yield Button("Desmarcar Todos", id="btn-deselect-all")
                        yield Button("Importar Selecionados", variant="success", id="btn-confirm-import")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-path":
            path = event.value
            if os.path.exists(path):
                self.query_one("#manual-dir-tree", FolderTree).path = path

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Ao clicar na pasta, marcamos ela como selecionada."""
        self.selected_path = str(event.node.data)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-finish-all":
            self.dismiss(True)
        elif event.button.id == "btn-list-files":
            # Pega o caminho selecionado na árvore ou o que está no Input
            path = getattr(self, "selected_path", None) or self.query_one("#input-path").value
            if os.path.exists(path):
                self.show_files_for_selection(path)
        elif event.button.id == "btn-back":
            self.query_one("#manual-switcher").current = "step-select-folder"
        elif event.button.id == "btn-select-all":
            self.query_one("#manual-selection-list", SelectionList).select_all()
        elif event.button.id == "btn-deselect-all":
            self.query_one("#manual-selection-list", SelectionList).deselect_all()
        elif event.button.id == "btn-confirm-import":
            self.run_import()

    def show_files_for_selection(self, path: str) -> None:
        switcher = self.query_one("#manual-switcher")
        selection_list = self.query_one("#manual-selection-list", SelectionList)
        selection_list.clear_options()
        
        all_files = list(self.app.scanner.iter_media_files(path))
        if not all_files:
            self.app.notify("Nenhum arquivo de vídeo encontrado!", severity="warning")
            return

        with SessionLocal() as db:
            existing_paths = {row[0] for row in db.query(MediaItem.file).all()}
            options = [Selection(os.path.basename(f), f) for f in all_files if f not in existing_paths]
            
            if not options:
                self.app.notify("Todos os arquivos já estão cadastrados.", severity="information")
                return
            
            selection_list.add_options(options)
            switcher.current = "step-select-files"

    def run_import(self) -> None:
        selected_files = self.query_one("#manual-selection-list", SelectionList).selected
        if not selected_files:
            self.app.notify("Selecione ao menos um arquivo!", severity="error")
            return

        import_count = 0
        with SessionLocal() as db:
            for f_path in selected_files:
                duration = self.app.scanner.get_media_duration(f_path)
                if duration > 0:
                    folder = self.app.scanner.get_or_create_folder(db, f_path, auto_scan=False)
                    new_item = MediaItem(
                        name=os.path.splitext(os.path.basename(f_path))[0],
                        file=f_path,
                        duration=duration,
                        folder_id=folder.id
                    )
                    db.add(new_item)
                    import_count += 1
            db.commit()
            
        self.app.notify(f"Sucesso! {import_count} mídias adicionadas.", severity="success")
        # RETORNA PARA A SELEÇÃO DE PASTA PARA PODER ADICIONAR MAIS
        self.query_one("#manual-switcher").current = "step-select-folder"
