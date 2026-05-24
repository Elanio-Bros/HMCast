from textual.widgets import DataTable


class PaginationMixin:
    """Mixin para paginação com scroll infinito em DataTables da TUI.

    Fornece estados e métodos reutilizáveis de paginação.
    As subclasses devem implementar ``load_page()`` com a lógica
    específica de consulta ao banco e preenchimento da tabela.

    Uso::

        class MyView(PaginationMixin, Vertical):
            def load_page(self) -> None:
                ...
    """

    # ── Estados da Paginação ──────────────────────────────────────────
    current_offset: int = 0
    page_size: int = 100
    has_more: bool = True
    is_loading: bool = False

    # ── Métodos Públicos ──────────────────────────────────────────────

    def reset_pagination(self) -> None:
        """Reinicia a paginação (offset = 0, has_more = True) e limpa a tabela."""
        self.current_offset = 0
        self.has_more = True
        try:
            table = self.query_one(DataTable)
            table.clear()
        except Exception:
            pass

    def check_scroll_for_pagination(self) -> None:
        """Verifica se o scroll ou cursor chegou ao final da tabela
        e dispara ``load_page()`` se necessário."""
        if not self.has_more or self.is_loading:
            return

        try:
            table = self.query_one(DataTable)
            at_bottom_scroll = table.scroll_y >= table.max_scroll_y - 10
            at_bottom_cursor = (
                table.cursor_row is not None
                and table.cursor_row >= table.row_count - 10
            )
            if at_bottom_scroll or at_bottom_cursor:
                self.load_page()
        except Exception:
            pass
