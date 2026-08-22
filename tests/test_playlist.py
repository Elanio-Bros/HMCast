from datetime import time
from app.channel import ChannelRuntime
from app.models import Channels, MediaItem, ChannelSchedule
from app.enums import PlaylistItemRole
import random


class DummyMedia(MediaItem):
    pass


def make_contents(n=5):
    """Helper: cria N itens de conteúdo AUTO."""
    return [
        {
            "media": DummyMedia(id=i+1, name=f"Epi {i+1}", duration=20, file=f"ep{i+1}.mp4"),
            "role": PlaylistItemRole.AUTO,
            "playlist_item_id": i+1
        }
        for i in range(n)
    ]


def test_build_session_timeline_ordering():
    """Valida ordem rígida: Abertura → Miolo rotacionado → Encerramento."""
    channel_obj = Channels(id=1, name="Test TV", type="TV")
    runtime = ChannelRuntime(channel_obj)

    m_opening = {"media": DummyMedia(id=10, name="Abertura", duration=10, file="abertura.mp4"), "role": PlaylistItemRole.OPENING, "playlist_item_id": 10}
    m_content1 = {"media": DummyMedia(id=2, name="Epi 1", duration=20, file="ep1.mp4"), "role": PlaylistItemRole.AUTO, "playlist_item_id": 2}
    m_content2 = {"media": DummyMedia(id=3, name="Epi 2", duration=20, file="ep2.mp4"), "role": PlaylistItemRole.AUTO, "playlist_item_id": 3}
    m_content3 = {"media": DummyMedia(id=4, name="Epi 3", duration=20, file="ep3.mp4"), "role": PlaylistItemRole.AUTO, "playlist_item_id": 4}
    m_closing = {"media": DummyMedia(id=11, name="Encerramento", duration=10, file="encerramento.mp4"), "role": PlaylistItemRole.CLOSING, "playlist_item_id": 11}

    openings = [m_opening]
    contents = [m_content1, m_content2, m_content3]
    closings = [m_closing]

    # idx=0: Abertura → Ep1 → Ep2 → Ep3 → Encerramento
    timeline = runtime.build_session_timeline(openings, contents, closings, current_item_index=0)
    assert len(timeline) == 5
    assert timeline[0]["role"] == PlaylistItemRole.OPENING
    assert timeline[1]["media"].name == "Epi 1"
    assert timeline[2]["media"].name == "Epi 2"
    assert timeline[3]["media"].name == "Epi 3"
    assert timeline[-1]["role"] == PlaylistItemRole.CLOSING

    # idx=1 (rotação): Abertura → Ep2 → Ep3 → Ep1 → Encerramento
    timeline_rotated = runtime.build_session_timeline(openings, contents, closings, current_item_index=1)
    assert timeline_rotated[1]["media"].name == "Epi 2"
    assert timeline_rotated[2]["media"].name == "Epi 3"
    assert timeline_rotated[3]["media"].name == "Epi 1"
    assert timeline_rotated[-1]["role"] == PlaylistItemRole.CLOSING

    # Sem abertura/encerramento, idx=2
    timeline_pure = runtime.build_session_timeline([], contents, [], current_item_index=2)
    assert len(timeline_pure) == 3
    assert timeline_pure[0]["media"].name == "Epi 3"
    assert timeline_pure[1]["media"].name == "Epi 1"
    assert timeline_pure[2]["media"].name == "Epi 2"


def test_shuffle_is_deterministic_same_day():
    """
    Shuffle usa semente de data+playlist_id+channel_id.
    Na mesma execução (mesma data), a ordem deve ser sempre igual.
    """
    from datetime import datetime

    contents = make_contents(5)
    seed = f"{datetime.now().date()}_1_1"

    # Aplica o mesmo algoritmo do channel.py duas vezes
    shuffled_a = list(contents)
    random.Random(seed).shuffle(shuffled_a)

    shuffled_b = list(contents)
    random.Random(seed).shuffle(shuffled_b)

    # As ordens devem ser idênticas (determinísticas)
    names_a = [c["media"].name for c in shuffled_a]
    names_b = [c["media"].name for c in shuffled_b]
    assert names_a == names_b


def test_shuffle_differs_from_original_order():
    """Shuffle deve (com alta probabilidade) mudar a ordem original."""
    from datetime import datetime

    contents = make_contents(8)
    original_names = [c["media"].name for c in contents]

    seed = f"{datetime.now().date()}_42_7"
    shuffled = list(contents)
    random.Random(seed).shuffle(shuffled)
    shuffled_names = [c["media"].name for c in shuffled]

    # Com 8 itens, a probabilidade de ser igual à original é 1/8! ≈ 0.00025%
    assert shuffled_names != original_names


def test_shuffle_preserves_all_items():
    """Shuffle não deve perder nem duplicar episódios."""
    from datetime import datetime

    contents = make_contents(6)
    original_names = set(c["media"].name for c in contents)

    seed = f"{datetime.now().date()}_99_3"
    shuffled = list(contents)
    random.Random(seed).shuffle(shuffled)
    shuffled_names = set(c["media"].name for c in shuffled)

    assert shuffled_names == original_names


# ─────────────────────────────────────────────────────────────────────────────
# Testes de conflito de agendamento OVERNIGHT (atravessa meia-noite)
# ─────────────────────────────────────────────────────────────────────────────

def test_schedule_conflict_overnight(db):
    """Agendamento overnight (23:00–02:00) deve conflitar com horários que cruzam meia-noite."""
    from app.models import Channels, ChannelSchedule

    channel = Channels(name="Canal Overnight")
    db.add(channel)
    db.commit()

    # Agendamento overnight: 23:00 até 02:00 (passa da meia-noite) nas segundas
    sch = ChannelSchedule(
        channel_id=channel.id,
        start_time=time(23, 0),
        end_time=time(2, 0),
        weekdays=["mon"]
    )
    db.add(sch)
    db.commit()

    # Deve conflitar: 01:00–03:00 na terça (está dentro do bloco overnight que começou na segunda às 23:00)
    conflict = ChannelSchedule.check_conflict(
        db, channel.id,
        time(1, 0), time(3, 0),
        weekdays=["tue"]
    )
    assert conflict is not None

    # Não deve conflitar: 03:00–05:00 (fora do bloco overnight)
    no_conflict = ChannelSchedule.check_conflict(
        db, channel.id,
        time(3, 0), time(5, 0),
        weekdays=["mon"]
    )
    assert no_conflict is None


def test_schedule_conflict_by_month_day(db):
    """Agendamento por dia do mês deve conflitar apenas no mesmo dia do mês."""
    from app.models import Channels, ChannelSchedule

    channel = Channels(name="Canal Mensal")
    db.add(channel)
    db.commit()

    # Agendamento dia 15 do mês
    sch = ChannelSchedule(
        channel_id=channel.id,
        start_time=time(10, 0),
        end_time=time(12, 0),
        month_days=[15]
    )
    db.add(sch)
    db.commit()

    # Conflito no dia 15 (sobreposição de horário)
    conflict = ChannelSchedule.check_conflict(
        db, channel.id,
        time(11, 0), time(13, 0),
        month_days=[15]
    )
    assert conflict is not None

    # Sem conflito no dia 16
    no_conflict = ChannelSchedule.check_conflict(
        db, channel.id,
        time(11, 0), time(13, 0),
        month_days=[16]
    )
    assert no_conflict is None
