import pytest
import sys
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# ─────────────────────────────────────────────────────────────────────────────
# BANCO DE DADOS DE TESTE EM ARQUIVO
#
# Usamos um arquivo temporário (não :memory:) para que múltiplas conexões
# independentes (do db fixture E da TUI internamente) enxerguem os mesmos dados.
# ─────────────────────────────────────────────────────────────────────────────

_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_file.close()
TEST_DATABASE_URL = f"sqlite:///{_test_db_file.name}"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Cria todas as tabelas antes da sessão de testes e remove ao final."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.unlink(_test_db_file.name)
    except Exception:
        pass


@pytest.fixture
def db():
    """
    Fixture para testes de lógica pura (CRUD, Core).
    Usa rollback automático ao final — os dados NÃO são visíveis em outras conexões.
    Perfeito para testes isolados sem interação com a TUI.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_committed():
    """
    Fixture para testes de TUI que precisam de dados visíveis em outras conexões.
    Commita os dados de verdade e os remove manualmente ao final do teste.
    Use apenas quando a TUI precisa ler dados pré-inseridos.
    """
    session = TestingSessionLocal()
    inserted_ids = {}  # rastreia o que foi inserido para limpar depois

    yield session, inserted_ids

    # Limpeza: remove todos os objetos da sessão que foram commitos
    session.close()

    # Limpa completamente as tabelas usadas pelos testes de TUI para evitar contaminação
    cleanup_session = TestingSessionLocal()
    try:
        from app.models import Channels, Playlist, ChannelSchedule
        cleanup_session.query(ChannelSchedule).delete()
        cleanup_session.query(Channels).delete()
        cleanup_session.query(Playlist).delete()
        cleanup_session.commit()
    except Exception:
        cleanup_session.rollback()
    finally:
        cleanup_session.close()


@pytest.fixture(autouse=True)
def mock_app_database(monkeypatch):
    """
    Substitui o SessionLocal do app pela versão de testes em TODOS os pontos.

    Como os modais da TUI fazem `from app.database import SessionLocal` em runtime
    dentro de funções, precisamos patchear o módulo `app.database` como fonte
    canônica. O Python sempre resolve `from X import Y` buscando `Y` no módulo `X`
    no momento da chamada — portanto, patchear `database.SessionLocal` é suficiente
    para qualquer importação subsequente.
    """
    from app import database
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)

    # Cobre módulos que já fizeram `from app.database import SessionLocal` na carga
    for mod_name, mod in list(sys.modules.items()):
        if mod is not None and "app" in mod_name and hasattr(mod, "SessionLocal"):
            try:
                monkeypatch.setattr(mod, "SessionLocal", TestingSessionLocal)
            except (AttributeError, TypeError):
                pass
