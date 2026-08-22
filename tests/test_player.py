import os
import tempfile
import shutil
import pytest
from app.channel import ChannelRuntime
from app.models import Channels


def test_get_next_start_number_empty_dir():
    """Garante que start_number começa em 0 se o diretório estiver vazio."""
    temp_dir = tempfile.mkdtemp()
    try:
        channel = Channels(id=1, name="Test TV")
        runtime = ChannelRuntime(channel)
        # Substitui a pasta do canal pela pasta temporária de testes
        runtime.channel_folder = temp_dir

        start_num = runtime._get_next_start_number()
        assert start_num == 0
    finally:
        shutil.rmtree(temp_dir)


def test_get_next_start_number_with_segments():
    """Garante que start_number retorna o maior segmento + 1."""
    temp_dir = tempfile.mkdtemp()
    try:
        channel = Channels(id=2, name="Test TV 2")
        runtime = ChannelRuntime(channel)
        runtime.channel_folder = temp_dir

        # Cria segmentos fakes
        open(os.path.join(temp_dir, "seg_0.ts"), "w").close()
        open(os.path.join(temp_dir, "seg_1.ts"), "w").close()
        open(os.path.join(temp_dir, "seg_5.ts"), "w").close()
        # Arquivo que não segue o padrão
        open(os.path.join(temp_dir, "outro_arquivo.ts"), "w").close()

        start_num = runtime._get_next_start_number()
        # O maior é 5, então o próximo deve ser 6
        assert start_num == 6
    finally:
        shutil.rmtree(temp_dir)
