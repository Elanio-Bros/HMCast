from app.channel import ChannelRuntime
from app.models import Channels


def test_calculate_clock_sync():
    """Testa os cenários básicos com 3 episódios de 10 minutos cada."""
    channel_obj = Channels(id=1, name="Test TV")
    runtime = ChannelRuntime(channel_obj)

    timeline = [
        {"duration": 600.0, "media_name": "Ep1"},
        {"duration": 600.0, "media_name": "Ep2"},
        {"duration": 600.0, "media_name": "Ep3"},
    ]

    # Teste 1: No começo (0s)
    idx, offset = runtime.calculate_clock_sync(timeline, 0.0)
    assert idx == 0
    assert offset == 0.0

    # Teste 2: Metade do primeiro episódio (300s)
    idx, offset = runtime.calculate_clock_sync(timeline, 300.0)
    assert idx == 0
    assert offset == 300.0

    # Teste 3: Exatamente no início do segundo episódio (600s)
    idx, offset = runtime.calculate_clock_sync(timeline, 600.0)
    assert idx == 1
    assert offset == 0.0

    # Teste 4: No meio do segundo episódio (900s)
    idx, offset = runtime.calculate_clock_sync(timeline, 900.0)
    assert idx == 1
    assert offset == 300.0

    # Teste 5: Estourou o tempo total (2000s > 1800s total)
    # A timeline faz loop via módulo: 2000 % 1800 = 200s → Ep1, offset 200s
    idx, offset = runtime.calculate_clock_sync(timeline, 2000.0)
    assert idx == 0
    assert offset == 200.0


def test_clock_sync_last_second_of_episode():
    """Testa o último segundo de um episódio — deve ainda ser o episódio atual."""
    channel_obj = Channels(id=2, name="Test TV 2")
    runtime = ChannelRuntime(channel_obj)

    timeline = [
        {"duration": 100.0, "media_name": "Ep1"},
        {"duration": 200.0, "media_name": "Ep2"},
    ]

    # O último segundo do Ep1 (99s) ainda é o Ep1
    idx, offset = runtime.calculate_clock_sync(timeline, 99.9)
    assert idx == 0
    assert abs(offset - 99.9) < 0.001


def test_clock_sync_variable_durations():
    """Testa com episódios de durações diferentes — abertura curta + conteúdos longos."""
    channel_obj = Channels(id=3, name="Test TV 3")
    runtime = ChannelRuntime(channel_obj)

    # Abertura: 30s, Ep1: 1800s (30min), Encerramento: 60s
    timeline = [
        {"duration": 30.0,   "media_name": "Abertura"},
        {"duration": 1800.0, "media_name": "Ep1"},
        {"duration": 60.0,   "media_name": "Encerramento"},
    ]

    # Dentro da abertura (15s)
    idx, offset = runtime.calculate_clock_sync(timeline, 15.0)
    assert idx == 0
    assert offset == 15.0

    # Início do Ep1 (30s = exatamente após abertura)
    idx, offset = runtime.calculate_clock_sync(timeline, 30.0)
    assert idx == 1
    assert offset == 0.0

    # No meio do Ep1 (30s de abertura + 900s de ep = 930s)
    idx, offset = runtime.calculate_clock_sync(timeline, 930.0)
    assert idx == 1
    assert offset == 900.0

    # Início do Encerramento (30 + 1800 = 1830s)
    idx, offset = runtime.calculate_clock_sync(timeline, 1830.0)
    assert idx == 2
    assert offset == 0.0


def test_clock_sync_single_item():
    """Timeline com apenas 1 item — qualquer tempo dentro deve retornar idx=0."""
    channel_obj = Channels(id=4, name="Test TV 4")
    runtime = ChannelRuntime(channel_obj)

    timeline = [{"duration": 3600.0, "media_name": "Filme Único"}]

    idx, offset = runtime.calculate_clock_sync(timeline, 0.0)
    assert idx == 0

    idx, offset = runtime.calculate_clock_sync(timeline, 1800.0)
    assert idx == 0
    assert offset == 1800.0
