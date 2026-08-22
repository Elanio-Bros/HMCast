from datetime import time, timedelta
from app.models import Channels, ChannelSchedule, Playlist, PlaylistItem, MediaItem
from app.enums import PlaylistItemRole

def test_create_channel(db):
    new_channel = Channels(name="Test Channel", type="TV")
    db.add(new_channel)
    db.commit()

    saved_channel = db.query(Channels).filter_by(name="Test Channel").first()
    assert saved_channel is not None
    assert saved_channel.id == 1
    assert saved_channel.type == "TV"

def test_channel_schedule_conflict(db):
    channel = Channels(name="Schedule Channel")
    db.add(channel)
    db.commit()

    # Adiciona agendamento das 10:00 as 12:00
    sch1 = ChannelSchedule(
        channel_id=channel.id,
        start_time=time(10, 0),
        end_time=time(12, 0),
        weekdays=["mon", "tue", "wed"]
    )
    db.add(sch1)
    db.commit()

    # Tenta conflitar: 11:00 as 13:00 na segunda-feira (mon)
    conflict_msg = ChannelSchedule.check_conflict(
        db, channel.id, time(11, 0), time(13, 0), weekdays=["mon"]
    )
    assert conflict_msg is not None
    assert "Conflito" in conflict_msg

    # Tenta não conflitar: 13:00 as 14:00
    conflict_msg2 = ChannelSchedule.check_conflict(
        db, channel.id, time(13, 0), time(14, 0), weekdays=["mon"]
    )
    assert conflict_msg2 is None

def test_playlist_calc_duration(db):
    playlist = Playlist(name="Test Playlist")
    db.add(playlist)
    db.commit()

    # Mídia 1 (60s)
    m1 = MediaItem(name="Video 1", file="test1.mp4", duration=60)
    # Mídia 2 (120s) com cortes, vamos simular que ele tem skips (ignorar final 10s)
    m2 = MediaItem(name="Video 2", file="test2.mp4", duration=120, skips={"finish": {"start": "00:01:50"}})
    db.add_all([m1, m2])
    db.commit()

    p_item1 = PlaylistItem(playlist_id=playlist.id, media_id=m1.id, position=0, role="FULL")
    p_item2 = PlaylistItem(playlist_id=playlist.id, media_id=m2.id, position=1, role="HEAD")
    db.add_all([p_item1, p_item2])
    db.commit()

    total_duration = Playlist.calc_total_duration(db, playlist.id)
    # m1: 60s
    # m2: tem 120s mas "finish" starts at 1:50 (110s). Com role="HEAD", ele não mostra finish (corta no 110s).
    # Total = 60 + 110 = 170s.
    assert total_duration == 170


# ─────────────────────────────────────────────────────────────────────────────
# SUBTAREFA 1 — ALTA PRIORIDADE: get_cut_times() com todos os papéis
# ─────────────────────────────────────────────────────────────────────────────

def make_media(duration=120, intro_end="00:00:30", finish_start="00:01:50"):
    """Helper: cria um MediaItem com skips de intro e finish."""
    from app.models import MediaItem
    return MediaItem(
        id=99, name="Test Media", file="test.mp4", duration=duration,
        skips={
            "intro":  {"end": intro_end},
            "finish": {"start": finish_start}
        }
    )


def test_get_cut_times_role_full():
    """FULL: mostra TUDO — intro e finish. Sem cortes."""
    media = make_media()
    start, end = media.get_cut_times(PlaylistItemRole.FULL, is_first=True, is_last=True)
    assert start == 0.0
    assert end == 120.0  # duração total, sem cortar o finish


def test_get_cut_times_role_head():
    """HEAD: mostra intro (início do vídeo), mas CORTA o finish."""
    media = make_media()  # intro_end=30s, finish_start=110s
    start, end = media.get_cut_times(PlaylistItemRole.HEAD, is_first=False, is_last=False)
    assert start == 0.0    # não pula a intro
    assert end == 110.0    # corta antes do finish (1:50 = 110s)


def test_get_cut_times_role_tail():
    """TAIL: PULA a intro, mas mostra o finish (encerramento)."""
    media = make_media()  # intro_end=30s, finish_start=110s
    start, end = media.get_cut_times(PlaylistItemRole.TAIL, is_first=False, is_last=False)
    assert start == 30.0   # pula os 30s de intro
    assert end == 120.0    # mostra o finish completo até o fim


def test_get_cut_times_role_auto_middle():
    """AUTO no meio da lista: PULA intro e CORTA finish."""
    media = make_media()
    start, end = media.get_cut_times(PlaylistItemRole.AUTO, is_first=False, is_last=False)
    assert start == 30.0   # pula intro
    assert end == 110.0    # corta finish


def test_get_cut_times_role_auto_first():
    """AUTO no PRIMEIRO item: mostra intro, mas corta finish."""
    media = make_media()
    start, end = media.get_cut_times(PlaylistItemRole.AUTO, is_first=True, is_last=False)
    assert start == 0.0    # é o primeiro, então MOSTRA a intro
    assert end == 110.0    # não é o último, então CORTA o finish


def test_get_cut_times_role_auto_last():
    """AUTO no ÚLTIMO item: pula intro, mas mostra finish."""
    media = make_media()
    start, end = media.get_cut_times(PlaylistItemRole.AUTO, is_first=False, is_last=True)
    assert start == 30.0   # não é o primeiro, então PULA a intro
    assert end == 120.0    # é o último, então MOSTRA o finish


def test_get_cut_times_role_auto_only():
    """AUTO sendo o ÚNICO item (first=True e last=True): mostra tudo."""
    media = make_media()
    start, end = media.get_cut_times(PlaylistItemRole.AUTO, is_first=True, is_last=True)
    assert start == 0.0    # é o primeiro → mostra intro
    assert end == 120.0    # é o último → mostra finish


def test_get_cut_times_no_skips():
    """Mídia sem skips: retorna 0 até duração total independente do papel."""
    from app.models import MediaItem
    media = MediaItem(id=1, name="Plain", file="plain.mp4", duration=300, skips=None)
    start, end = media.get_cut_times(PlaylistItemRole.AUTO, is_first=False, is_last=False)
    assert start == 0.0
    assert end == 300.0


def test_playlist_calc_duration_with_intermediate_cuts(db):
    """Valida que cortes intermediários (cuts no meio) são subtraídos corretamente."""
    playlist = Playlist(name="Playlist com Cuts")
    db.add(playlist)
    db.commit()

    # Mídia de 300s com:
    # - intro: 0s–30s (show em FULL)
    # - finish: 270s–300s (show em FULL)
    # - cut intermediário: 100s–130s (30s a remover)
    m = MediaItem(
        name="Episodio com Cut", file="ep.mp4", duration=300,
        skips={
            "cuts": [{"start": "00:01:40", "end": "00:02:10"}]  # 100s–130s = 30s de cut
        }
    )
    db.add(m)
    db.commit()

    p_item = PlaylistItem(playlist_id=playlist.id, media_id=m.id, position=0, role="FULL")
    db.add(p_item)
    db.commit()

    total = Playlist.calc_total_duration(db, playlist.id)
    # 300s - 30s de cut intermediário = 270s
    assert total == 270

