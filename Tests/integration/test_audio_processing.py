"""
音频处理集成测试
"""
import pytest
import sys
import os
import tempfile
import wave
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Src'))

from Processors.AudioCore import AudioCore


@pytest.mark.integration
class TestAudioProcessing:
    """音频处理集成测试类"""

    def create_test_wav(self, path, duration=1.0, sample_rate=44100):
        """创建测试WAV文件"""
        num_samples = int(duration * sample_rate)
        data = []
        for i in range(num_samples):
            # 生成简单的正弦波
            import math
            t = i / sample_rate
            value = math.sin(2 * math.pi * 440 * t) * 0.5
            data.append(int(value * 32767))

        with wave.open(path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack('<' + 'h' * len(data), *data))

    def test_full_audio_process(self, temp_output_dir):
        """测试完整音频处理流程"""
        # 创建测试文件
        affirmation_path = os.path.join(temp_output_dir, 'test_affirmation.wav')
        background_path = os.path.join(temp_output_dir, 'test_background.wav')
        output_path = os.path.join(temp_output_dir, 'output.wav')

        self.create_test_wav(affirmation_path, duration=2.0)
        self.create_test_wav(background_path, duration=5.0)

        # 设置参数
        params = {
            'affirmation_file': affirmation_path,
            'background_file': background_path,
            'output_path': output_path,
            'volume': 0.0,
            'speed': 1.0,
            'reverse': False,
            'overlay_times': 2,
            'overlay_interval': 0.5,
            'volume_decrease': 3.0,
            'overlay_stagger_mode': False,
            'background_volume': -10.0,
            'freq_track_enabled': False,
            'isochronic_enabled': True,
            'isochronic_freq': '10',
            'isochronic_volume': -25.0,
            'isochronic_shape': 'sine',
            'output_format': 'WAV'
        }

        # 创建处理器
        audio_core = AudioCore(params)

        # 执行处理
        result = audio_core.process(params=params)

        # 验证输出文件存在
        assert result is not None
        assert os.path.exists(output_path)

    def test_isochronic_with_different_frequencies(self, temp_output_dir):
        """测试不同频率的等时音"""
        affirmation_path = os.path.join(temp_output_dir, 'test.wav')
        output_path_4hz = os.path.join(temp_output_dir, 'output_4hz.wav')
        output_path_10hz = os.path.join(temp_output_dir, 'output_10hz.wav')
        output_path_40hz = os.path.join(temp_output_dir, 'output_40hz.wav')

        self.create_test_wav(affirmation_path, duration=1.0)

        frequencies = [
            ('4', output_path_4hz),   # Theta
            ('10', output_path_10hz), # Alpha
            ('40', output_path_40hz)  # Gamma
        ]

        for freq, out_path in frequencies:
            params = {
                'affirmation_file': affirmation_path,
                'background_file': '',
                'output_path': out_path,
                'volume': 0.0,
                'speed': 1.0,
                'reverse': False,
                'overlay_times': 1,
                'overlay_interval': 1.0,
                'volume_decrease': 0.0,
                'overlay_stagger_mode': False,
                'background_volume': 0.0,
                'freq_track_enabled': False,
                'isochronic_enabled': True,
                'isochronic_freq': freq,
                'isochronic_volume': -20.0,
                'isochronic_shape': 'sine',
                'output_format': 'WAV'
            }

            audio_core = AudioCore(params)
            result = audio_core.process(params=params)

            assert result is not None
            assert os.path.exists(out_path)

    def test_isochronic_shapes_integration(self, temp_output_dir):
        """测试不同波形的等时音集成"""
        affirmation_path = os.path.join(temp_output_dir, 'test.wav')
        self.create_test_wav(affirmation_path, duration=1.0)

        shapes = ['sine', 'square', 'triangle']

        for shape in shapes:
            output_path = os.path.join(temp_output_dir, f'output_{shape}.wav')

            params = {
                'affirmation_file': affirmation_path,
                'background_file': '',
                'output_path': output_path,
                'volume': 0.0,
                'speed': 1.0,
                'reverse': False,
                'overlay_times': 1,
                'overlay_interval': 1.0,
                'volume_decrease': 0.0,
                'overlay_stagger_mode': False,
                'background_volume': 0.0,
                'freq_track_enabled': False,
                'isochronic_enabled': True,
                'isochronic_freq': '10',
                'isochronic_volume': -20.0,
                'isochronic_shape': shape,
                'output_format': 'WAV'
            }

            audio_core = AudioCore(params)
            result = audio_core.process(params=params)

            assert result is not None
            assert os.path.exists(output_path)
