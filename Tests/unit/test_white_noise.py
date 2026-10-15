"""
白噪音生成功能单元测试
"""
import pytest
import sys
import os
import wave
import struct
from types import SimpleNamespace

# 添加Src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Src'))

from Processors.AudioCore import AudioCore
from UI.NoiseManager import NoiseManager


class FakeLineEdit:
    """模拟 QLineEdit，仅用于测试取文本逻辑"""

    def __init__(self, text=""):
        self._text = text

    def text(self):
        return self._text


class TestWhiteNoiseGeneration:
    """AudioCore.generate_white_noise 测试类"""

    @pytest.fixture
    def audio_core(self):
        return AudioCore()

    def test_generate_creates_wav_with_expected_format(self, audio_core, tmp_path):
        """生成的WAV格式应与请求的参数一致"""
        output_path = str(tmp_path / "noise.wav")

        result_path, seed = audio_core.generate_white_noise(
            output_path, duration=0.1, seed=1234,
            sample_rate=8000, channels=1, sample_width=2)

        assert result_path == output_path
        assert seed == 1234
        assert os.path.exists(output_path)

        with wave.open(output_path, 'rb') as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 8000
            assert wf.getnframes() == 800

    def test_same_seed_is_reproducible(self, audio_core, tmp_path):
        """相同种子应生成完全一致的文件"""
        first = str(tmp_path / "first.wav")
        second = str(tmp_path / "second.wav")

        audio_core.generate_white_noise(first, 0.05, seed=42, sample_rate=8000)
        audio_core.generate_white_noise(second, 0.05, seed=42, sample_rate=8000)

        with open(first, 'rb') as f1, open(second, 'rb') as f2:
            assert f1.read() == f2.read()

    def test_different_seed_produces_different_audio(self, audio_core, tmp_path):
        """不同种子应生成不同的音频数据"""
        first = str(tmp_path / "first.wav")
        second = str(tmp_path / "second.wav")

        audio_core.generate_white_noise(first, 0.05, seed=1, sample_rate=8000)
        audio_core.generate_white_noise(second, 0.05, seed=2, sample_rate=8000)

        with wave.open(first, 'rb') as wf1, wave.open(second, 'rb') as wf2:
            assert wf1.readframes(wf1.getnframes()) != wf2.readframes(wf2.getnframes())

    def test_string_seed_is_supported(self, audio_core, tmp_path):
        """非数字种子也应可用且可复现"""
        first = str(tmp_path / "first.wav")
        second = str(tmp_path / "second.wav")

        _, seed = audio_core.generate_white_noise(first, 0.05, seed="my-seed", sample_rate=8000)
        audio_core.generate_white_noise(second, 0.05, seed="my-seed", sample_rate=8000)

        assert seed == "my-seed"
        with open(first, 'rb') as f1, open(second, 'rb') as f2:
            assert f1.read() == f2.read()

    def test_random_seed_when_not_provided(self, audio_core, tmp_path):
        """未提供种子时应随机生成并返回"""
        output_path = str(tmp_path / "noise.wav")

        _, seed = audio_core.generate_white_noise(output_path, 0.05, sample_rate=8000)

        assert isinstance(seed, int)
        assert 0 <= seed <= 2 ** 32 - 1

    def test_progress_callback_reaches_100(self, audio_core, tmp_path):
        """进度回调应单调递增并以100结束"""
        output_path = str(tmp_path / "noise.wav")
        progress_values = []

        audio_core.generate_white_noise(
            output_path, duration=1.0, seed=7, sample_rate=8000,
            chunk_size=1000, progress_callback=progress_values.append)

        assert progress_values[-1] == 100
        assert progress_values == sorted(progress_values)
        assert all(0 <= v <= 100 for v in progress_values)

    def test_creates_missing_output_directory(self, audio_core, tmp_path):
        """输出目录不存在时应自动创建"""
        output_path = str(tmp_path / "nested" / "dir" / "noise.wav")

        audio_core.generate_white_noise(output_path, 0.05, seed=3, sample_rate=8000)

        assert os.path.exists(output_path)

    def test_invalid_duration_raises(self, audio_core, tmp_path):
        """时长非正数时应抛出 ValueError"""
        output_path = str(tmp_path / "noise.wav")

        with pytest.raises(ValueError):
            audio_core.generate_white_noise(output_path, duration=0, seed=1)
        with pytest.raises(ValueError):
            audio_core.generate_white_noise(output_path, duration=-1, seed=1)

    def test_samples_within_amplitude_and_random(self, audio_core, tmp_path):
        """采样值应在振幅范围内且非全零"""
        output_path = str(tmp_path / "noise.wav")
        amplitude = 0.5

        audio_core.generate_white_noise(
            output_path, duration=0.05, seed=9, sample_rate=8000,
            amplitude=amplitude)

        with wave.open(output_path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
        samples = struct.unpack('<%dh' % (len(frames) // 2), frames)

        limit = int(amplitude * 32767) + 1
        assert all(abs(s) <= limit for s in samples)
        assert any(s != 0 for s in samples)
        assert len(set(samples)) > 1

    def test_block_size_does_not_change_output(self, audio_core, tmp_path):
        """分块大小不应影响生成结果"""
        first = str(tmp_path / "first.wav")
        second = str(tmp_path / "second.wav")

        audio_core.generate_white_noise(first, 0.05, seed=5, sample_rate=8000, chunk_size=100)
        audio_core.generate_white_noise(second, 0.05, seed=5, sample_rate=8000, chunk_size=1000)

        with open(first, 'rb') as f1, open(second, 'rb') as f2:
            assert f1.read() == f2.read()


class TestNoiseManagerHelpers:
    """NoiseManager 路径与种子解析逻辑测试类"""

    @pytest.fixture
    def noise_manager(self):
        return NoiseManager(SimpleNamespace())

    def test_parse_seed(self, noise_manager):
        assert noise_manager._parse_seed("") is None
        assert noise_manager._parse_seed("   ") is None
        assert noise_manager._parse_seed("42") == 42
        assert noise_manager._parse_seed("  42  ") == 42
        assert noise_manager._parse_seed("abc") == "abc"

    def test_resolve_output_path_defaults_to_bgm(self, noise_manager):
        noise_manager.main_window.white_noise_output = FakeLineEdit("")

        path = noise_manager._resolve_output_path("/project/demo")

        assert path == os.path.normpath("/project/demo/Assets/BGM.wav")

    def test_resolve_output_path_appends_wav(self, noise_manager):
        noise_manager.main_window.white_noise_output = FakeLineEdit("/tmp/my-noise")

        assert noise_manager._resolve_output_path("/project/demo") == os.path.normpath("/tmp/my-noise.wav")

    def test_resolve_output_path_relative_to_project(self, noise_manager):
        noise_manager.main_window.white_noise_output = FakeLineEdit("Assets/custom.wav")

        path = noise_manager._resolve_output_path("/project/demo")

        assert path == os.path.normpath("/project/demo/Assets/custom.wav")

    def test_resolve_output_path_keeps_absolute(self, noise_manager):
        noise_manager.main_window.white_noise_output = FakeLineEdit("/other/noise.wav")

        assert noise_manager._resolve_output_path("/project/demo") == os.path.normpath("/other/noise.wav")

    def test_get_default_output_path_without_project(self, noise_manager):
        noise_manager.main_window.get_current_project_dir = lambda: None

        assert noise_manager.get_default_output_path() == ""

    def test_get_default_output_path_with_project(self, noise_manager):
        noise_manager.main_window.get_current_project_dir = lambda: "/project/demo"

        assert noise_manager.get_default_output_path() == os.path.normpath("/project/demo/Assets/BGM.wav")
