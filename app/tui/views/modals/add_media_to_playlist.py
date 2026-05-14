from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import SelectionList, Button, Label, Static, Select, Tree
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal
from app.enums import PlaylistItemRole


class AddMediaToPlaylistModal(ModalScreen[bool]):
    """Modal para Adicionar Múltiplas Mídias a uma Playlist."""

    def __init__(self, playlist_id: int):
        super().__init__()
        self.playlist_id = playlist_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("VINCULAR MÍDIAS À PLAYLIST", id="modal-title")
            
            with Horizontal(id="m-pl-workspace"):
                with Vertical(classes="tree-column"):
                    yield Label("Pastas:", classes="section-label")
                    yield Tree("BIBLIOTECAS", id="pl-folder-tree")
                
                with Vertical(classes="list-column"):
                    yield Label("Vídeos da Pasta (ESPAÇO para marcar):", classes="section-label")
                    yield SelectionList[int](id="selection-media")
            
            with Vertical(classes="input-group"):
                yield Label("Papel na Playlist (Para todos os selecionados):")
                yield Select([
                    ("Inteligente (AUTO)", PlaylistItemRole.AUTO.value),
                    ("Completo (FULL)", PlaylistItemRole.FULL.value),
                    ("Com Abertura (HEAD)", PlaylistItemRole.HEAD.value),
                    ("Com Encerramento (TAIL)", PlaylistItemRole.TAIL.value),
                    ("Apenas Conteúdo (BODY)", PlaylistItemRole.BODY.value),
                    ("Abertura Fixa (OPENING)", PlaylistItemRole.OPENING.value),
                    ("Encerramento Fixo (CLOSING)", PlaylistItemRole.CLOSING.value)
                ], id="select-role", value=PlaylistItemRole.AUTO.value)
            
            yield Label("", id="m-pl-error-message", classes="error-text")
            
            with Horizontal(id="modal-actions"):
                yield Button("Selecionar Tudo", variant="primary", id="btn-m-pl-select-all")
                yield Button("Adicionar Selecionados", variant="success", id="btn-m-pl-save")
                yield Button("Cancelar", variant="error", id="btn-m-pl-cancel")

    def on_mount(self) -> None:
        tree = self.query_one("#pl-folder-tree", Tree)
        tree.show_root = False
        self.reload_folder_tree()
        self.query_one("#selection-media", SelectionList).clear_options()

    def reload_folder_tree(self) -> None:
        from app.database import SessionLocal
        from app.models import MediaFolder
        
        tree = self.query_one("#pl-folder-tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()
        
        with SessionLocal() as db:
            folders = db.query(MediaFolder).filter(MediaFolder.parent_id == None).all()
            for f in folders:
                node = root.add(f.name, data=f.id)
                self._add_subfolders_to_node(db, node, f.id)

    def _add_subfolders_to_node(self, db, node, parent_id):
        from app.models import MediaFolder
        subfolders = db.query(MediaFolder).filter(MediaFolder.parent_id == parent_id).all()
        for sf in subfolders:
            subnode = node.add(sf.name, data=sf.id)
            self._add_subfolders_to_node(db, subnode, sf.id)

    def _get_all_subfolder_ids(self, db, parent_id) -> list[int]:
        from app.models import MediaFolder
        ids = [parent_id]
        subfolders = db.query(MediaFolder.id).filter(MediaFolder.parent_id == parent_id).all()
        for (sf_id,) in subfolders:
            ids.extend(self._get_all_subfolder_ids(db, sf_id))
        return ids

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        folder_id = event.node.data
        if not folder_id:
            return
            
        selection_list = self.query_one("#selection-media", SelectionList)
        selection_list.clear_options()
        
        from app.database import SessionLocal
        from app.models import MediaItem
        
        with SessionLocal() as db:
            all_ids = self._get_all_subfolder_ids(db, folder_id)
            medias = db.query(MediaItem).filter(MediaItem.folder_id.in_(all_ids)).order_by(MediaItem.name).all()
            
            options = [Selection(m.name, m.id) for m in medias]
            if not options:
                self.app.notify("Nenhum vídeo nesta pasta.", severity="warning")
            else:
                selection_list.add_options(options)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-m-pl-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-m-pl-save":
            self.save_items()
        elif event.button.id == "btn-m-pl-select-all":
            self.action_select_all()

    def action_select_all(self) -> None:
        selection_list = self.query_one("#selection-media", SelectionList)
        if not selection_list.options:
            return
            
        if len(selection_list.selected) == len(selection_list.options):
            selection_list.deselect_all()
        else:
            selection_list.select_all()

    def save_items(self) -> None:
        from app.database import SessionLocal
        from app.models import PlaylistItem
        from sqlalchemy import func
        
        selected_ids = self.query_one("#selection-media", SelectionList).selected
        role = self.query_one("#select-role", Select).value
        error_lab = self.query_one("#m-pl-error-message", Label)
        
        if not selected_ids:
            error_lab.update("Selecione ao menos uma mídia!")
            return

        with SessionLocal() as db:
            # Busca a última posição atual na playlist
            max_pos = db.query(func.max(PlaylistItem.position)).filter_by(playlist_id=self.playlist_id).scalar()
            current_pos = (max_pos + 1) if max_pos is not None else 0
            
            for media_id in selected_ids:
                new_item = PlaylistItem(
                    playlist_id=self.playlist_id,
                    media_id=media_id,
                    position=current_pos,
                    role=role
                )
                db.add(new_item)
                current_pos += 1 # Incrementa a posição para o próximo vídeo
            
            db.commit()
            
        self.dismiss(True)
