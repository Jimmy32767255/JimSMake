"""
AudioCore 单元测试
"""
import pytest
import sys
import os

# 添加Src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Src'))

from Processors.AudioCore import AudioCore


class TestAudioCore:
    """AudioCore 测试类"""

    @pytest.fixture
    def audio_core(self):
        """创建 AudioCore 实例"""
        return AudioCore()

    @pytest.fixture
    def sample_params(self):
        """示例参数"""
        return {
            'affirmation_file': 'test.wav',
            'background_file': 'bg.wav',
            'output_path': 'output.wav',
            'volume': 0.0,
            'speed': 1.0,
            'reverse': False,
            'overlay_times': 1,
            'overlay_interval': 1.0,
            'volume_decrease': 0.0,
            'overlay_stagger_mode': False,
            'background_volume': 0.0,
            'freq_track_enabled': False,
            'isochronic_enabled': False,
            'output_format': 'WAV'
        }

    def test_init(self, audio_core):
        """测试初始化"""
        assert audio_core is not None
        assert audio_core.params == {}
        assert audio_core.is_cancelled is False

    def test_set_params(self, audio_core, sample_params):
        """测试设置参数"""
        audio_core.set_params(sample_params)
        assert audio_core.params == sample_params

    def test_cancel(self, audio_core):
        """测试取消功能"""
        assert audio_core.check_cancelled() is False
        audio_core.cancel()
        assert audio_core.check_cancelled() is True

    def test_resample_audio(self, audio_core):
        """测试音频重采样"""
        # 创建测试数据
        data = [0.0, 0.5, 1.0, 0.5, 0.0]
        src_rate = 1000
        dst_rate = 2000

        result = audio_core._resample_audio(data, src_rate, dst_rate)

        # 验证结果长度
        expected_length = int(len(data) * dst_rate / src_rate)
        assert len(result) == expected_length

    def test_change_speed_same_speed(self, audio_core):
        """测试相同速度不改变数据"""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = audio_core._change_speed(data, 1.0, 1000)
        assert result == data

    def test_apply_isochronic_tones_disabled(self, audio_core):
        """测试等时音禁用时返回原数据"""
        audio_data = {
            'data': [0.0, 0.1, 0.2],
            'sample_rate': 44100,
            'channels': 1,
            'sample_width': 2
        }
        params = {'isochronic_enabled': False}

        result = audio_core.apply_isochronic_tones(audio_data, params)

        assert result == audio_data

    def test_apply_isochronic_tones_enabled(self, audio_core):
        """测试等时音启用时处理数据"""
        audio_data = {
            'data': [0.0, 0.1, 0.2, 0.3, 0.4],
            'sample_rate': 44100,
            'channels': 1,
            'sample_width': 2
        }
        params = {
            'isochronic_enabled': True,
            'isochronic_freq': '10',
            'isochronic_volume': -20.0,
            'isochronic_shape': 'sine'
        }

        result = audio_core.apply_isochronic_tones(audio_data, params)

        # 验证返回的是新的audio_data
        assert 'data' in result
        assert len(result['data']) == len(audio_data['data'])

    def test_array_to_wav_and_back(self, audio_core):
        """测试音频数组与WAV数据转换"""
        original_data = [0.0, 0.5, -0.5, 0.25, -0.25]

        # 转换为WAV数据
        wav_data = audio_core._array_to_wav(original_data, 2)
        assert isinstance(wav_data, bytes)

        # 转换回数组
        result = audio_core._wav_to_array(wav_data, 2, 1)

        # 验证长度相同
        assert len(result) == len(original_data)

    @pytest.mark.parametrize("shape", ['sine', 'square', 'triangle'])
    def test_isochronic_shapes(self, audio_core, shape):
        """测试等时音不同波形"""
        audio_data = {
            'data': [0.0] * 100,
            'sample_rate': 44100,
            'channels': 1,
            'sample_width': 2
        }
        params = {
            'isochronic_enabled': True,
            'isochronic_freq': '10',
            'isochronic_volume': -20.0,
            'isochronic_shape': shape
        }

        result = audio_core.apply_isochronic_tones(audio_data, params)

        assert 'data' in result
        assert len(result['data']) == len(audio_data['data'])
