from textual.app import ComposeResult
from textual.widgets import Static, Button, DataTable, Input, Tree, ProgressBar
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Markdown
from app.database import SessionLocal
from app.models import MediaItem, MediaFolder
import os

class MediaView(Vertical):
    """View de Gestão de Mídias estilo Explorador de Arquivos."""
    
    selected_folder_id = None
    
    # Estados da Paginação Real
    current_search = ""
    current_offset = 0
    page_size = 100
    has_more = True
    is_loading = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="view-header"):
            yield Static("GERENCIAMENTO DE MÍDIAS", classes="view-title")
        
        with Horizontal(id="search-bar"):
            yield Input(placeholder="Buscar mídia por nome...", id="input-search-media")

        yield ProgressBar(id="scan-progress", show_percentage=True, show_eta=True)

        with Horizontal(id="media-workspace"):
            # Árvore de Pastas (Esquerda)
            yield Tree("BIBLIOTECAS", id="folder-tree")
            # Tabela de Mídias (Centro)
            yield DataTable(id="media-table")
            # Painel de Detalhes (Direita)
            with VerticalScroll(id="details-panel"):
                yield Static("DETALHES", id="details-title")
                yield Static("", id="details-content")

        with Horizontal(classes="action-bar"):
            yield Button("Adicionar", variant="primary", id="btn-add-media", classes="btn-action")
            yield Button("Info. Cutouts", variant="success", id="btn-manage-cutouts", classes="btn-action")
            yield Button("Scan Global", variant="warning", id="btn-scan-global", classes="btn-action")
            yield Button("Auto-Scan ON/OFF", id="btn-toggle-scan", classes="btn-action")
            yield Button("Renomear", id="btn-rename", classes="btn-action")
            yield Button("Excluir", variant="error", id="btn-delete", classes="btn-action")
            yield Button("Voltar", id="btn-back-home", classes="btn-action")

    def on_mount(self) -> None:
        table = self.query_one("#media-table", DataTable)
        table.add_columns("ID", "Nome")
        table.zebra_stripes = True
        table.cursor_type = "row"
        
        tree = self.query_one("#folder-tree", Tree)
        tree.show_root = False  # Oculta a pasta virtual "BIBLIOTECAS"
        
        self.reload_folder_tree()
        self.reload_data()
        self.last_active_widget = tree # Começa com a árvore por padrão
        self.query_one("#scan-progress").display = False # Escondido por padrão
        self.query_one("#scan-progress").progress = 0
        
        # Inicia o Radar de Paginação (verifica a cada 0.5s se chegou no fim)
        self.set_interval(0.5, self.check_scroll_for_pagination)

    def check_scroll_for_pagination(self) -> None:
        """Verifica se o usuário rolou a tabela até o final para carregar mais dados."""
        if not self.has_more or self.is_loading:
            return
            
        try:
            table = self.query_one("#media-table", DataTable)
            # Verifica o scroll do mouse OU o cursor do teclado
            at_bottom_scroll = table.scroll_y >= table.max_scroll_y - 10
            at_bottom_cursor = (table.cursor_row is not None and table.cursor_row >= table.row_count - 10)
            
            if at_bottom_scroll or at_bottom_cursor:
                self.load_page()
        except Exception:
            pass

    def on_descendant_focus(self, event) -> None:
        """Sempre que um filho ganhar foco, lembramos dele se for Tree ou Table."""
        if isinstance(event.control, (Tree, DataTable)):
            self.last_active_widget = event.control

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Atualiza o painel de detalhes conforme o cursor navega pela tabela."""
        try:
            row_data = event.data_table.get_row_at(event.cursor_row)
            media_id = int(row_data[0])
            self._update_details_panel(media_id)
        except Exception:
            pass

    def _update_details_panel(self, media_id: int) -> None:
        """Busca os dados da mídia e renderiza o painel lateral."""
        with SessionLocal() as db:
            media = db.query(MediaItem).get(media_id)
            if not media:
                return

            skips = media.skips or {}
            duration = media.duration or 0
            h = duration // 3600
            m = (duration % 3600) // 60
            s = duration % 60
            dur_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

            sep = "─" * 33
            filename = os.path.basename(media.file)
            dirpath = os.path.dirname(media.file)

            lines = []
            lines.append(media.name)
            lines.append(sep)
            lines.append(f"Duração: {dur_str}")
            lines.append(f"Arquivo: {filename}")
            lines.append(f"Caminho: {dirpath}")
            lines.append("")

            if skips:
                lines.append(sep)
                lines.append("CORTES")
                lines.append("")

                intro = skips.get("intro")
                if intro:
                    lines.append("Abertura")
                    lines.append(f" Inicio: {intro.get('start', '?')}")
                    lines.append(f" Fim: {intro.get('end', '?')}")
                    lines.append("")

                finish = skips.get("finish")
                if finish:
                    lines.append("Créditos")
                    lines.append(f"  ▶ {finish.get('start', '?')}")
                    lines.append(f"  ◼ {finish.get('end', '?')}")
                    lines.append("")

                cuts = skips.get("cuts", [])
                if cuts:
                    lines.append(f"Outros ({len(cuts)})")
                    for i, cut in enumerate(cuts, 1):
                        lines.append(f"  [{i}] ▶ {cut.get('start','?')}")
                        lines.append(f"       ◼ {cut.get('end','?')}")
            else:
                lines.append(sep)
                lines.append("Sem cortes cadastrados.")

            self.query_one("#details-content", Static).update("\n".join(lines))


    def reload_folder_tree(self) -> None:
        """Carrega as pastas raízes do banco na árvore."""
        tree = self.query_one("#folder-tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()
        
        with SessionLocal() as db:
            # Pega apenas as pastas raízes (sem pai)
            folders = db.query(MediaFolder).filter(MediaFolder.parent_id == None).all()
            for f in folders:
                label = f" {f.name}"
                if f.auto_scan:
                    label = f" [A] {f.name}"
                
                node = root.add(label, data=f.id)
                self._add_subfolders_to_node(db, node, f.id)

    def _add_subfolders_to_node(self, db, node, parent_id):
        subfolders = db.query(MediaFolder).filter(MediaFolder.parent_id == parent_id).all()
        for sf in subfolders:
            label = f" {sf.name}"
            if sf.auto_scan:
                label = f" [A] {sf.name}"
            subnode = node.add(label, data=sf.id)
            self._add_subfolders_to_node(db, subnode, sf.id)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Filtra a tabela ao selecionar uma pasta na árvore."""
        self.selected_folder_id = event.node.data
        self.reload_data()

    def reload_data(self, search: str = "") -> None:
        """Limpa a tabela e reinicia a paginação do zero."""
        self.current_search = search
        self.current_offset = 0
        self.has_more = True
        
        table = self.query_one("#media-table", DataTable)
        table.clear()
        
        self.load_page()

    def load_page(self) -> None:
        """Carrega a próxima página (lote) de mídias e anexa na tabela."""
        if self.is_loading or not self.has_more:
            return
            
        self.is_loading = True
        table = self.query_one("#media-table", DataTable)
        
        with SessionLocal() as db:
            from app.models import MediaFolder
            query = db.query(
                MediaItem, 
                MediaFolder.path.label("folder_path")
            ).outerjoin(MediaFolder, MediaItem.folder_id == MediaFolder.id)
            
            if self.selected_folder_id:
                # Pega o ID da pasta e de todas as subpastas dela recursivamente
                all_ids = self._get_all_subfolder_ids(db, self.selected_folder_id)
                query = query.filter(MediaItem.folder_id.in_(all_ids))
            elif self.current_search:
                # Se não tem pasta selecionada, mas tem busca, procura em todo o banco
                query = query.filter(MediaItem.name.ilike(f"%{self.current_search}%"))
            else:
                # Sem pasta selecionada e sem busca: não mostra nada por padrão
                self.is_loading = False
                return
            
            if self.current_search and self.selected_folder_id:
                # Se tem pasta E busca, aplica a busca dentro da pasta
                query = query.filter(MediaItem.name.ilike(f"%{self.current_search}%"))
            
            # Puxa o lote exato com LIMIT e OFFSET
            items = query.order_by(MediaItem.id.desc()).offset(self.current_offset).limit(self.page_size).all()
            
            # Se voltou menos itens que o tamanho da página, chegamos no fim definitivo
            if len(items) < self.page_size:
                self.has_more = False
                
            self.current_offset += len(items)
            
            rows_to_add = []
            for item, folder_path in items:
                rows_to_add.append((str(item.id), item.name))

            try:
                table.add_rows(rows_to_add)
            except Exception as e:
                self.app.log(f"Erro ao adicionar linhas na tabela: {e}")
                
        self.is_loading = False

    def _get_all_subfolder_ids(self, db, parent_id) -> list[int]:
        """Retorna uma lista com o ID pai e todos os IDs de subpastas recursivamente."""
        ids = [parent_id]
        subfolders = db.query(MediaFolder.id).filter(MediaFolder.parent_id == parent_id).all()
        for (sf_id,) in subfolders:
            ids.extend(self._get_all_subfolder_ids(db, sf_id))
        return ids

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-search-media":
            self.reload_data(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-add-media":
            from app.tui.views.modals.add_media import AddMediaModal
            def check_result(success: bool):
                if success:
                    self.reload_folder_tree()
                    self.reload_data()
            self.app.push_screen(AddMediaModal(media_view=self), check_result)
        
        elif event.button.id == "btn-scan-global":
            progress_bar = self.query_one("#scan-progress", ProgressBar)
            progress_bar.display = True
            progress_bar.progress = 0
            
            async def run_global_scan_task():
                def update_progress(current, total):
                    self.app.call_from_thread(progress_bar.update, total=total, progress=current)

                with SessionLocal() as db:
                    # Pega apenas as pastas RAIZ (parent_id is None) que estão com Auto-Scan
                    folders = db.query(MediaFolder).filter(
                        MediaFolder.auto_scan == True,
                        MediaFolder.parent_id == None
                    ).all()
                    for f in folders:
                        self.app.scanner.scan_media_folder(f.path, progress_callback=update_progress)
                    
                    self.app.scanner.health_check_all_folders()
                
                # Lógica de conclusão dentro do worker
                def on_complete():
                    self.reload_data()
                    self.app.notify("Scan Global e Faxina concluídos!", severity="success")
                    progress_bar.display = False
                
                self.app.call_from_thread(on_complete)

            self.run_worker(run_global_scan_task(), thread=True)
            self.app.notify("Iniciando Scan Global em background...")

        elif event.button.id == "btn-toggle-scan":
            self.action_toggle_auto_scan()

        elif event.button.id == "btn-manage-cutouts":
            self.action_manage_cutouts()

        elif event.button.id == "btn-rename":
            self.action_rename_selected()

        elif event.button.id == "btn-delete":
            self.action_delete_selected()

    def action_manage_cutouts(self) -> None:
        focused = getattr(self, "last_active_widget", None)
        if isinstance(focused, DataTable):
            row_index = focused.cursor_row
            if row_index is not None:
                row_data = focused.get_row_at(row_index)
                media_id = int(row_data[0])
                from app.tui.views.modals.media_cutouts import MediaCutoutsModal
                
                def check_result(success: bool):
                    if success:
                        self.reload_data()
                        
                self.app.push_screen(MediaCutoutsModal(media_id=media_id), check_result)
        else:
            self.app.notify("Selecione um vídeo na tabela primeiro!", severity="warning")

    def action_toggle_auto_scan(self) -> None:
        """Alterna o auto_scan da biblioteca selecionada."""
        focused = getattr(self, "last_active_widget", None)
        if isinstance(focused, Tree):
            node = focused.cursor_node
            if node and node.data:
                folder_id = node.data
                with SessionLocal() as db:
                    folder = db.query(MediaFolder).get(folder_id)
                    if folder:
                        folder.auto_scan = not folder.auto_scan
                        db.commit()
                        self.reload_folder_tree()
                        status = "ativado" if folder.auto_scan else "desativado"
                        self.app.notify(f"Auto-Scan {status} para {folder.name}!")

    def action_rename_selected(self) -> None:
        """Ação para renomear o item focado (Pasta ou Mídia)."""
        # Usamos o widget que estava ativo antes do clique no botão
        focused = getattr(self, "last_active_widget", None)
        
        if isinstance(focused, Tree):
            node = focused.cursor_node
            if node and node.data:
                folder_id = node.data
                from app.tui.views.modals.prompt import PromptModal
                
                def do_rename(new_name: str):
                    if new_name:
                        with SessionLocal() as db:
                            folder = db.query(MediaFolder).get(folder_id)
                            if folder:
                                folder.name = new_name
                                db.commit()
                                self.reload_folder_tree()
                                self.app.notify("Biblioteca renomeada!")

                self.app.push_screen(PromptModal("Novo nome da Biblioteca:", initial_value=str(node.label)), do_rename)

        elif isinstance(focused, DataTable):
            row_index = focused.cursor_row
            if row_index is not None:
                row_data = focused.get_row_at(row_index)
                media_id = int(row_data[0])
                from app.tui.views.modals.prompt import PromptModal

                def do_rename_media(new_name: str):
                    if new_name:
                        with SessionLocal() as db:
                            item = db.query(MediaItem).get(media_id)
                            if item:
                                item.name = new_name
                                db.commit()
                                self.reload_data()
                                self.app.notify("Mídia renomeada!")

                self.app.push_screen(PromptModal("Novo nome da Mídia:", initial_value=row_data[1]), do_rename_media)

    def action_delete_selected(self) -> None:
        """Ação para excluir o item focado."""
        focused = getattr(self, "last_active_widget", None)

        if isinstance(focused, Tree):
            node = focused.cursor_node
            if node and node.data:
                with SessionLocal() as db:
                    folder = db.query(MediaFolder).get(self.selected_folder_id)
                    if folder:
                        # 1. Coleta TODOS os IDs de pastas (a atual e todas as subpastas)
                        all_folder_ids = self._get_all_subfolder_ids(db, folder.id)
                        
                        # 2. Busca TODAS as mídias vinculadas a essas pastas
                        all_items = db.query(MediaItem).filter(MediaItem.folder_id.in_(all_folder_ids)).all()
                        item_ids = [item.id for item in all_items]
                        
                        if item_ids:
                            # Remove referências em Playlists
                            from app.models import PlaylistItem
                            db.query(PlaylistItem).filter(PlaylistItem.media_id.in_(item_ids)).delete(synchronize_session=False)
                            # Remove as mídias
                            db.query(MediaItem).filter(MediaItem.id.in_(item_ids)).delete(synchronize_session=False)
                        
                        # 3. Remove todas as subpastas e a pasta principal
                        db.query(MediaFolder).filter(MediaFolder.id.in_(all_folder_ids)).delete(synchronize_session=False)
                        
                        db.commit()
                        self.app.notify(f"Pasta '{folder.name}' e todo seu conteúdo removidos.", severity="success")
                        self.selected_folder_id = None
                        self.reload_folder_tree()
                        self.reload_data()

        elif isinstance(focused, DataTable):
            row_index = focused.cursor_row
            if row_index is not None:
                row_data = focused.get_row_at(row_index)
                media_id = int(row_data[0])
                with SessionLocal() as db:
                    from app.models import PlaylistItem
                    db.query(PlaylistItem).filter(PlaylistItem.media_id == media_id).delete()
                    db.query(MediaItem).filter(MediaItem.id == media_id).delete()
                    db.commit()
                    self.reload_data()
    def start_folder_scan(self, path: str, m_progress=None):
        """Inicia o scan gerenciado pela própria MediaView, atualizando barras gêmeas."""
        progress_bar = self.query_one("#scan-progress", ProgressBar)
        progress_bar.display = True
        progress_bar.progress = 0
        
        def run_scan():
            def update_progress(current, total):
                self.app.call_from_thread(progress_bar.update, total=total, progress=current)
                if m_progress:
                    try:
                        self.app.call_from_thread(m_progress.update, total=total, progress=current)
                    except Exception: pass
                
            self.app.scanner.scan_media_folder(path, progress_callback=update_progress)
            
            def on_complete():
                self.app.notify(f"Pasta {os.path.basename(path)} importada com sucesso!", severity="success")
                try:
                    progress_bar.display = False
                    if m_progress:
                        try: m_progress.display = False
                        except Exception: pass
                    self.reload_folder_tree()
                    self.reload_data()
                except Exception as e:
                    self.app.notify(f"Erro ao atualizar view: {e}", severity="error")
                    
            self.app.call_from_thread(on_complete)
            
        self.run_worker(run_scan, thread=True)
        self.app.notify("Iniciando importação da pasta em background...")

    def start_manual_import(self, files: list[str], m_progress=None):
        """Inicia a importação manual gerenciada pela própria MediaView."""
        progress_bar = self.query_one("#scan-progress", ProgressBar)
        progress_bar.display = True
        progress_bar.progress = 0
        
        def run_import():
            import_count = 0
            with SessionLocal() as db:
                total = len(files)
                for i, f_path in enumerate(files):
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
                    
                    # Atualiza progresso a cada arquivo
                    self.app.call_from_thread(progress_bar.update, total=total, progress=i+1)
                    if m_progress:
                        try:
                            self.app.call_from_thread(m_progress.update, total=total, progress=i+1)
                        except Exception: pass
                db.commit()
            
            def on_complete():
                self.app.notify(f"Sucesso! {import_count} mídias adicionadas.", severity="success")
                try:
                    progress_bar.display = False
                    if m_progress:
                        try: m_progress.display = False
                        except Exception: pass
                    self.reload_folder_tree()
                    self.reload_data()
                except Exception as e:
                    self.app.notify(f"Erro ao atualizar view: {e}", severity="error")
                    
            self.app.call_from_thread(on_complete)
            
        self.run_worker(run_import, thread=True)
        self.app.notify("Importando arquivos em background...")
