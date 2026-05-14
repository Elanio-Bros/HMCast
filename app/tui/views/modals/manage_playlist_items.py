from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, DataTable, Label, Select
from textual.containers import Vertical, Horizontal
from app.enums import PlaylistItemRole
from app.database import SessionLocal
from app.models import PlaylistItem, MediaItem
import os

class ManagePlaylistItemsModal(ModalScreen[bool]):
    """Modal dedicado a organizar a grade, reordenar e trocar papéis."""

    def __init__(self, playlist_id: int):
        super().__init__()
        self.playlist_id = playlist_id
        self.marked_rows = set()  # IDs dos PlaylistItems marcados para mover em bloco

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static("GERENCIAR ITENS DA PLAYLIST", id="modal-title")
            
            yield Label("Use ESPAÇO para marcar/desmarcar vários itens para mover em bloco.")
            yield DataTable(id="manage-items-table")
            
            with Horizontal(classes="input-group"):
                yield Label("Alterar Papel do Focado:")
                yield Select([
                    ("Inteligente (AUTO)", PlaylistItemRole.AUTO.value),
                    ("Completo (FULL)", PlaylistItemRole.FULL.value),
                    ("Com Abertura (HEAD)", PlaylistItemRole.HEAD.value),
                    ("Com Encerramento (TAIL)", PlaylistItemRole.TAIL.value),
                    ("Apenas Conteúdo (BODY)", PlaylistItemRole.BODY.value),
                    ("Abertura Fixa (OPENING)", PlaylistItemRole.OPENING.value),
                    ("Encerramento Fixo (CLOSING)", PlaylistItemRole.CLOSING.value)
                ], id="select-item-role", prompt="Selecione um papel")

            with Horizontal(id="modal-actions"):
                yield Button("Selecionar Tudo", variant="success", id="btn-m-select-all")
                yield Button("Mover Subir", variant="primary", id="btn-m-up")
                yield Button("Mover Descer", variant="primary", id="btn-m-down")
                yield Button("Remover", variant="error", id="btn-m-remove")
                yield Button("Fechar", id="btn-m-close")

    def on_mount(self) -> None:
        table = self.query_one("#manage-items-table", DataTable)
        table.add_columns("M", "Pos", "Título", "Papel")
        table.zebra_stripes = True
        table.cursor_type = "row"
        self.reload_items()

    def reload_items(self) -> None:
        table = self.query_one("#manage-items-table", DataTable)
        # Salva o scroll e o cursor para não perder a posição
        scroll_y = table.scroll_y
        cursor_row = table.cursor_row
        
        table.clear()
        with SessionLocal() as db:
            items = (
                db.query(PlaylistItem, MediaItem)
                .join(MediaItem, MediaItem.id == PlaylistItem.media_id)
                .filter(PlaylistItem.playlist_id == self.playlist_id)
                .order_by(PlaylistItem.position.asc())
                .all()
            )
            
            for p_item, m_item in items:
                mark = "[X]" if p_item.id in self.marked_rows else "[ ]"
                table.add_row(
                    mark,
                    str(p_item.position),
                    m_item.name,
                    p_item.role,
                    key=str(p_item.id)
                )
        
        # Restaura posição
        table.scroll_y = scroll_y
        if cursor_row is not None:
            try: table.move_cursor(row=cursor_row)
            except: pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Sincroniza o seletor de papel e alterna a marcação ao clicar na linha."""
        item_id = int(event.row_key.value)
        
        # Alterna a marcação (Mouse click ou Enter)
        if item_id in self.marked_rows:
            self.marked_rows.remove(item_id)
        else:
            self.marked_rows.add(item_id)
            
        self.reload_items()
        
        with SessionLocal() as db:
            item = db.query(PlaylistItem).get(item_id)
            if item:
                self.query_one("#select-item-role", Select).value = item.role

    def on_select_changed(self, event: Select.Changed) -> None:
        """Salva o novo papel assim que alterado no seletor."""
        if event.select.id == "select-item-role" and event.value:
            table = self.query_one(DataTable)
            try:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                item_id = int(row_key.value)
                with SessionLocal() as db:
                    item = db.query(PlaylistItem).get(item_id)
                    if item and item.role != event.value:
                        item.role = event.value
                        db.commit()
                        self.reload_items()
            except: pass

    def on_key(self, event) -> None:
        """Atalho de teclado para marcar itens com Espaço."""
        if event.key == "space":
            table = self.query_one(DataTable)
            try:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                item_id = int(row_key.value)
                if item_id in self.marked_rows:
                    self.marked_rows.remove(item_id)
                else:
                    self.marked_rows.add(item_id)
                self.reload_items()
            except: pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-m-close":
            self.dismiss(True)
        elif event.button.id == "btn-m-select-all":
            self.action_select_all()
        elif event.button.id == "btn-m-up":
            self.action_move_items(up=True)
        elif event.button.id == "btn-m-down":
            self.action_move_items(up=False)
        elif event.button.id == "btn-m-remove":
            self.action_remove_items()

    def action_select_all(self) -> None:
        table = self.query_one(DataTable)
        all_ids = [int(row_key.value) for row_key in table.rows]
        
        if len(self.marked_rows) == len(all_ids) and len(all_ids) > 0:
            self.marked_rows.clear()
        else:
            self.marked_rows = set(all_ids)
            
        self.reload_items()

    def action_move_items(self, up: bool) -> None:
        """Move os itens marcados (ou o atual se nenhum marcado) para cima ou baixo."""
        table = self.query_one(DataTable)
        
        # Se nada estiver marcado, movemos apenas o focado
        ids_to_move = list(self.marked_rows)
        if not ids_to_move:
            try:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                ids_to_move = [int(row_key.value)]
            except: return

        with SessionLocal() as db:
            # Pega os objetos do banco e ordena por posição para mover na ordem certa
            items = db.query(PlaylistItem).filter(PlaylistItem.id.in_(ids_to_move)).all()
            items.sort(key=lambda x: x.position, reverse=not up)
            
            for item in items:
                new_pos = item.position - 1 if up else item.position + 1
                if new_pos < 0: continue
                
                # Troca com o vizinho que NÃO está no grupo de movimento
                neighbor = db.query(PlaylistItem).filter_by(
                    playlist_id=self.playlist_id, 
                    position=new_pos
                ).first()
                
                if neighbor and neighbor.id not in ids_to_move:
                    neighbor.position = item.position
                    item.position = new_pos
                elif not neighbor:
                    # Se não tem vizinho (ex: deletado ou fim da lista), apenas muda
                    item.position = new_pos
            
            db.commit()
            self.reload_items()

    def action_remove_items(self) -> None:
        """Remove itens marcados ou o atual."""
        table = self.query_one(DataTable)
        ids_to_remove = list(self.marked_rows)
        if not ids_to_remove:
            try:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                ids_to_remove = [int(row_key.value)]
            except: return

        with SessionLocal() as db:
            db.query(PlaylistItem).filter(PlaylistItem.id.in_(ids_to_remove)).delete(synchronize_session=False)
            db.commit()
            self.marked_rows.clear()
            self.reload_items()
