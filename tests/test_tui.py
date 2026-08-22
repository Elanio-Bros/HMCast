"""
Testes da TUI (Interface de Usuário).

Usamos o `app.run_test()` do Textual com `size=(220, 50)` para garantir que
todos os widgets caibam na área visível, evitando OutOfBounds.

O Pilot do Textual usa:
  - pilot.click("#id")       → Clicar em widget por seletor CSS
  - pilot.press("a", "b")   → Simular teclas (digitação)
  - pilot.pause()            → Aguardar mensagens assíncronas serem processadas
"""
import pytest
from textual.widgets import DataTable, Label
from textual.screen import ModalScreen

from app.tui.app import HMCli
from app.models import Channels, Playlist


async def _type_into(pilot, selector: str, text: str):
    """Helper: foca em um Input e digita tecla a tecla."""
    await pilot.click(selector)
    for char in text:
        await pilot.press(char)


# ─────────────────────────────────────────────────────────────────────────────
# TESTES DE MONTAGEM E NAVEGAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_app_mounts(mock_app_database):
    """Verifica se a app TUI inicializa sem erros e com título correto."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        assert pilot.app.screen is not None
        assert pilot.app.title == "HMC"


@pytest.mark.asyncio
async def test_tui_navigate_to_channels(mock_app_database):
    """Verifica se clicar em 'Canais' no menu home muda a view."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        from textual.widgets import ContentSwitcher
        switcher = pilot.app.screen.query_one(ContentSwitcher)
        assert switcher.current == "channels-manager"


@pytest.mark.asyncio
async def test_tui_channels_table_loads(db_committed, mock_app_database):
    """Verifica se a tabela de canais carrega registros do banco."""
    session, _ = db_committed
    channel = Channels(name="Canal Teste TUI", type="TV", identifier="TUI-01")
    session.add(channel)
    session.commit()

    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        table = pilot.app.screen.query_one("#channels-table", DataTable)
        assert table.row_count >= 1


@pytest.mark.asyncio
async def test_tui_navigate_to_playlists(mock_app_database):
    """Verifica se clicar em 'Playlists' no menu home muda a view."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-playlists")
        await pilot.pause()

        from textual.widgets import ContentSwitcher
        switcher = pilot.app.screen.query_one(ContentSwitcher)
        assert switcher.current == "playlists-manager"


# ─────────────────────────────────────────────────────────────────────────────
# TESTES DE MODAL DE CANAL
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_open_add_channel_modal(mock_app_database):
    """Verifica se o modal de adicionar canal abre corretamente."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        await pilot.click("#btn-add-channel")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ModalScreen)


@pytest.mark.asyncio
async def test_tui_add_channel_cancel_closes_modal(mock_app_database):
    """Verifica se cancelar o modal de canal fecha a tela modal."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        await pilot.click("#btn-add-channel")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ModalScreen)

        await pilot.click("#btn-cancel")
        await pilot.pause()

        assert not isinstance(pilot.app.screen, ModalScreen)


@pytest.mark.asyncio
async def test_tui_esc_closes_modal(mock_app_database):
    """Verifica se pressionar ESC fecha o modal (Regra de Ouro)."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        await pilot.click("#btn-add-channel")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ModalScreen)

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(pilot.app.screen, ModalScreen)


@pytest.mark.asyncio
async def test_tui_add_channel_saves_to_db(db, mock_app_database):
    """Verifica se preencher e salvar o modal de canal persiste no banco."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        await pilot.click("#btn-add-channel")
        await pilot.pause()

        # Digita o identificador
        await _type_into(pilot, "#channel-identifier", "TEST-99")
        await pilot.pause()

        # Digita o nome do canal
        await _type_into(pilot, "#channel-name", "Canal Test 99")
        await pilot.pause()

        await pilot.click("#btn-save")
        await pilot.pause()

        # Verifica no banco
        saved = db.query(Channels).filter_by(identifier="TEST-99").first()
        assert saved is not None
        assert saved.name == "Canal Test 99"
        assert saved.type == "TV"


@pytest.mark.asyncio
async def test_tui_add_channel_duplicate_identifier_blocked(db_committed, mock_app_database):
    """
    Verifica que o sistema bloqueia a criação de um canal com identificador duplicado.
    Usa db_committed para que a TUI (conexão interna própria) enxergue o canal pré-existente.
    """
    session, _ = db_committed
    existing = Channels(name="Canal Existente", type="TV", identifier="DUP-01")
    session.add(existing)
    session.commit()

    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        await pilot.click("#btn-add-channel")
        await pilot.pause()

        await _type_into(pilot, "#channel-identifier", "DUP-01")
        await _type_into(pilot, "#channel-name", "Canal Duplicado")

        await pilot.click("#btn-save")
        await pilot.pause()

    # Verifica que continua existindo apenas 1 canal com DUP-01 (não foi duplicado)
    count = session.query(Channels).filter_by(identifier="DUP-01").count()
    assert count == 1, f"Esperado 1 canal com DUP-01, mas encontrou {count}"




# ─────────────────────────────────────────────────────────────────────────────
# TESTES DE MODAL DE PLAYLIST
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_open_add_playlist_modal(mock_app_database):
    """Verifica se o modal de criar playlist abre corretamente."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-playlists")
        await pilot.pause()

        await pilot.click("#btn-add-playlist")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ModalScreen)


@pytest.mark.asyncio
async def test_tui_add_playlist_empty_name_shows_error(mock_app_database):
    """Verifica se tentar criar uma playlist sem nome exibe mensagem de erro."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-playlists")
        await pilot.pause()

        await pilot.click("#btn-add-playlist")
        await pilot.pause()

        # Tenta salvar sem preencher o nome
        await pilot.click("#btn-pl-save")
        await pilot.pause()

        # O label de erro deve ter conteúdo não-vazio
        error_label = pilot.app.screen.query_one("#pl-error-message", Label)
        label_text = str(error_label.render())
        assert label_text.strip() != ""

        # Modal permanece aberto
        assert isinstance(pilot.app.screen, ModalScreen)
        await pilot.press("escape")


@pytest.mark.asyncio
async def test_tui_add_playlist_saves_to_db(db, mock_app_database):
    """Verifica se criar uma playlist via modal persiste no banco."""
    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-playlists")
        await pilot.pause()

        await pilot.click("#btn-add-playlist")
        await pilot.pause()

        await _type_into(pilot, "#pl-name", "Playlist TUI Test")
        await pilot.pause()

        await pilot.click("#btn-pl-save")
        await pilot.pause()

        saved = db.query(Playlist).filter_by(name="Playlist TUI Test").first()
        assert saved is not None
        assert saved.shuffle is False


# ─────────────────────────────────────────────────────────────────────────────
# TESTES DE OPERAÇÕES DE CANAL (TOGGLE, DELETE, EDIT)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_channel_toggle_active(db_committed, mock_app_database):
    """Verifica se o botão Ligar/Desligar altera o status do canal no banco."""
    session, _ = db_committed
    channel = Channels(name="Canal Toggle", type="TV", identifier="TOG-01", active=True)
    session.add(channel)
    session.commit()

    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        # Foca no DataTable e clica em ligar/desligar (afeta a linha selecionada - a primeira)
        await pilot.click("#channels-table")
        await pilot.click("#btn-toggle-channel")
        await pilot.pause()

        # Verifica se o status mudou para inativo (active=False)
        # Recarrega a instância para pegar o estado mais recente
        session.expire(channel)
        assert channel.active is False


@pytest.mark.asyncio
async def test_tui_channel_delete(db_committed, mock_app_database):
    """Verifica se o botão Excluir remove o canal do banco de dados."""
    session, _ = db_committed
    channel = Channels(name="Canal Delete", type="TV", identifier="DEL-01")
    session.add(channel)
    session.commit()

    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        await pilot.click("#channels-table")
        await pilot.click("#btn-delete-channel")
        await pilot.pause()

        # Verifica se o canal foi removido
        count = session.query(Channels).filter_by(identifier="DEL-01").count()
        assert count == 0


@pytest.mark.asyncio
async def test_tui_channel_edit(db_committed, mock_app_database):
    """Verifica se é possível detalhar e editar um canal salvando no banco."""
    session, _ = db_committed
    channel = Channels(name="Canal Original", type="TV", identifier="EDT-01")
    session.add(channel)
    session.commit()

    async with HMCli().run_test(size=(220, 50)) as pilot:
        await pilot.click("#card-channels")
        await pilot.pause()

        await pilot.click("#channels-table")
        # Abre tela de detalhes
        await pilot.click("#btn-detail-channel")
        await pilot.pause()

        # Abre modal de edição
        await pilot.click("#btn-detail-edit")
        await pilot.pause()

        # Altera o nome
        pilot.app.screen.query_one("#channel-name").value = ""
        await _type_into(pilot, "#channel-name", "Canal Editado")
        await pilot.pause()

        await pilot.click("#btn-save")
        await pilot.pause()

        # Verifica se o canal foi atualizado
        session.expire(channel)
        assert channel.name == "Canal Editado"

