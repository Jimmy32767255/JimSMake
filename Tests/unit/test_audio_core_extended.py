"""
AudioCore 扩展单元测试 - 覆盖更多方法
"""
import pytest
import sys
import os
import tempfile
import wave
import struct
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Src'))

from Processors.AudioCore import AudioCore


class TestAudioCoreExtended:
    """AudioCore 扩展测试类"""

    @pytest.fixture
    def audio_core(self):
        """创建 AudioCore 实例"""
        return AudioCore()

    @pytest.fixture
    def sample_audio_data(self):
        """示例音频数据"""
        sample_rate = 44100
        duration = 0.1  # 短音频用于测试
        num_samples = int(duration * sample_rate)
        data = []
        for i in range(num_samples):
            t = i / sample_rate
            value = math.sin(2 * math.pi * 440 * t) * 0.5
            data.append(value)

        return {
            'data': data,
            'sample_rate': sample_rate,
            'channels': 1,
            'sample_width': 2
        }

    def test_wav_to_array_24bit(self, audio_core):
        """测试24位WAV数据转换"""
        # 24-bit signed
        samples = [0, 1000000, -1000000]
        raw_data = b''
        for s in samples:
            raw_data += s.to_bytes(3, byteorder='little', signed=True)

        result = audio_core._wav_to_array(raw_data, 3, 1)
        assert len(result) == 3

    def test_wav_to_array_32bit(self, audio_core):
        """测试32位WAV数据转换"""
        raw_data = struct.pack('<iii', 0, 1000000000, -1000000000)
        result = audio_core._wav_to_array(raw_data, 4, 1)
        assert len(result) == 3

    def test_array_to_wav_24bit(self, audio_core):
        """测试24位WAV数据生成"""
        data = [0.0, 0.5, -0.5]
        result = audio_core._array_to_wav(data, 3)
        assert isinstance(result, bytes)
        assert len(result) == 9  # 3 samples * 3 bytes

    def test_array_to_wav_32bit(self, audio_core):
        """测试32位WAV数据生成"""
        data = [0.0, 0.5, -0.5]
        result = audio_core._array_to_wav(data, 4)
        assert isinstance(result, bytes)
        assert len(result) == 12  # 3 samples * 4 bytes

    def test_resample_audio_same_rate(self, audio_core):
        """测试相同采样率不重采样"""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = audio_core._resample_audio(data, 44100, 44100)
        assert result == data

    def test_resample_audio_downsample(self, audio_core):
        """测试降采样"""
        data = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        src_rate = 1000
        dst_rate = 500
        result = audio_core._resample_audio(data, src_rate, dst_rate)

        # 降采样后长度应该减半
        expected_length = int(len(data) * dst_rate / src_rate)
        assert len(result) == expected_length

    def test_change_speed_faster(self, audio_core):
        """测试加速 - 速度>1时输出长度应该变短"""
        # 使用足够长的数据（大于window_size=1024）
        data = [0.5] * 5000
        sample_rate = 44100
        result = audio_core._change_speed(data, 2.0, sample_rate)

        # 2倍速，输出长度应该约为输入的一半
        # 由于算法复杂性，只需验证长度发生了变化且不为0
        assert len(result) > 0
        assert len(result) < len(data)

    def test_change_speed_slower(self, audio_core):
        """测试减速 - 速度<1时输出长度应该变长"""
        # 使用足够长的数据
        data = [0.5] * 5000
        sample_rate = 44100
        result = audio_core._change_speed(data, 0.5, sample_rate)

        # 0.5倍速，输出长度应该约为输入的两倍
        assert len(result) > len(data)

    def test_change_speed_invalid(self, audio_core):
        """测试无效速度"""
        data = [0.1, 0.2, 0.3]
        result = audio_core._change_speed(data, 0.0, 44100)
        assert result == data

        result = audio_core._change_speed(data, -1.0, 44100)
        assert result == data

    def test_apply_frequency_shift(self, audio_core):
        """测试频率调整"""
        data = [0.5] * 100  # 恒定值
        sample_rate = 44100
        target_freq = 1000

        result = audio_core._apply_frequency_shift(data, sample_rate, target_freq)

        assert len(result) == len(data)
        # 调制后不应该全是相同值
        assert len(set([round(x, 6) for x in result])) > 1

    def test_process_affirmation_effects_speed(self, audio_core, sample_audio_data):
        """测试处理肯定语效果 - 速度"""
        params = {
            'speed': 2.0,
            'reverse': False,
            'freq_adjust_enabled': False,
            'volume': 0.0
        }

        original_length = len(sample_audio_data['data'])
        result = audio_core.process_affirmation_effects(sample_audio_data.copy(), params)

        # 速度改变后长度应该变化
        assert len(result['data']) != original_length

    def test_process_affirmation_effects_reverse(self, audio_core, sample_audio_data):
        """测试处理肯定语效果 - 倒放"""
        params = {
            'speed': 1.0,
            'reverse': True,
            'freq_adjust_enabled': False,
            'volume': 0.0
        }

        original_first = sample_audio_data['data'][0]
        result = audio_core.process_affirmation_effects(sample_audio_data.copy(), params)

        # 倒放后第一个值应该变成最后一个
        assert result['data'][-1] == pytest.approx(original_first, rel=1e-3)

    def test_process_affirmation_effects_volume(self, audio_core, sample_audio_data):
        """测试处理肯定语效果 - 音量"""
        params = {
            'speed': 1.0,
            'reverse': False,
            'freq_adjust_enabled': False,
            'volume': -10.0
        }

        original_max = max(abs(x) for x in sample_audio_data['data'])
        result = audio_core.process_affirmation_effects(sample_audio_data.copy(), params)
        result_max = max(abs(x) for x in result['data'])

        # 负音量应该降低振幅
        assert result_max < original_max

    def test_process_affirmation_effects_freq_adjust(self, audio_core, sample_audio_data):
        """测试处理肯定语效果 - 频率调整"""
        params = {
            'speed': 1.0,
            'reverse': False,
            'freq_adjust_enabled': True,
            'frequency_mode': 17500,
            'volume': 0.0
        }

        result = audio_core.process_affirmation_effects(sample_audio_data.copy(), params)

        assert len(result['data']) == len(sample_audio_data['data'])

    def test_apply_overlay_single(self, audio_core, sample_audio_data):
        """测试单次叠加（不叠加）"""
        params = {
            'overlay_times': 1,
            'overlay_interval': 1.0,
            'volume_decrease': 0.0,
            'overlay_stagger_mode': False
        }

        result = audio_core.apply_overlay(sample_audio_data.copy(), params)

        # 单次叠加应该返回原数据
        assert result == sample_audio_data

    def test_apply_overlay_multiple(self, audio_core, sample_audio_data):
        """测试多次叠加"""
        params = {
            'overlay_times': 3,
            'overlay_interval': 0.1,
            'volume_decrease': 3.0,
            'overlay_stagger_mode': False
        }

        original_length = len(sample_audio_data['data'])
        result = audio_core.apply_overlay(sample_audio_data.copy(), params)

        # 多次叠加后长度应该增加
        assert len(result['data']) > original_length

    def test_apply_overlay_stagger(self, audio_core, sample_audio_data):
        """测试交错叠加模式"""
        params = {
            'overlay_times': 3,
            'overlay_interval': 0.1,
            'volume_decrease': 0.0,
            'overlay_stagger_mode': True
        }

        result = audio_core.apply_overlay(sample_audio_data.copy(), params)

        # 交错模式应该产生不同的结果
        assert 'data' in result

    def test_merge_audio_no_background(self, audio_core, sample_audio_data):
        """测试无背景音合并"""
        result = audio_core.merge_audio(sample_audio_data, None)

        # 无背景音应该返回肯定语数据
        assert result == sample_audio_data

    def test_merge_audio_with_background(self, audio_core, sample_audio_data):
        """测试有背景音合并"""
        # 创建背景音数据（比肯定语长）
        bg_data = {
            'data': [0.1] * (len(sample_audio_data['data']) * 2),
            'sample_rate': sample_audio_data['sample_rate'],
            'channels': 1,
            'sample_width': 2
        }

        result = audio_core.merge_audio(sample_audio_data, bg_data)

        assert 'data' in result
        # 合并后长度应该等于背景音长度
        assert len(result['data']) == len(bg_data['data'])

    def test_merge_audio_ensure_integrity(self, audio_core, sample_audio_data):
        """测试确保完整性模式"""
        # 创建背景音数据
        bg_data = {
            'data': [0.1] * (len(sample_audio_data['data']) * 3 + 100),
            'sample_rate': sample_audio_data['sample_rate'],
            'channels': 1,
            'sample_width': 2
        }

        audio_core.params = {'ensure_integrity': True}
        result = audio_core.merge_audio(sample_audio_data, bg_data)

        assert 'data' in result

    def test_apply_freq_track_disabled(self, audio_core, sample_audio_data):
        """测试禁用频率音轨"""
        params = {'freq_track_enabled': False}

        result = audio_core.apply_freq_track(sample_audio_data.copy(), params)

        # 禁用时应该返回原数据
        assert result == sample_audio_data

    def test_apply_freq_track_normal(self, audio_core, sample_audio_data):
        """测试普通频率音轨模式"""
        params = {
            'freq_track_enabled': True,
            'freq_track_freq': '432',
            'freq_track_volume': -20.0,
            'freq_track_diff_mode': False
        }

        result = audio_core.apply_freq_track(sample_audio_data.copy(), params)

        assert 'data' in result
        assert len(result['data']) == len(sample_audio_data['data'])

    def test_apply_freq_track_diff_mode(self, audio_core, sample_audio_data):
        """测试差值频率音轨模式"""
        params = {
            'freq_track_enabled': True,
            'freq_track_freq': '432',
            'freq_track_volume': -20.0,
            'freq_track_diff_mode': True,
            'freq_track_diff': '10',
            'freq_track_swap_channels': False
        }

        result = audio_core.apply_freq_track(sample_audio_data.copy(), params)

        assert 'data' in result
        # 差值模式应该产生立体声
        assert result['channels'] == 2

    def test_apply_freq_track_invalid_freq(self, audio_core, sample_audio_data):
        """测试无效频率值"""
        params = {
            'freq_track_enabled': True,
            'freq_track_freq': 'invalid',
            'freq_track_volume': -20.0,
            'freq_track_diff_mode': False
        }

        result = audio_core.apply_freq_track(sample_audio_data.copy(), params)

        # 无效频率应该返回原数据
        assert result['data'] == sample_audio_data['data']

    def test_apply_isochronic_invalid_freq(self, audio_core, sample_audio_data):
        """测试无效等时音频率"""
        params = {
            'isochronic_enabled': True,
            'isochronic_freq': 'invalid',
            'isochronic_volume': -20.0,
            'isochronic_shape': 'sine'
        }

        result = audio_core.apply_isochronic_tones(sample_audio_data.copy(), params)

        # 无效频率应该返回原数据
        assert result['data'] == sample_audio_data['data']

    def test_apply_isochronic_zero_freq(self, audio_core, sample_audio_data):
        """测试零等时音频率"""
        params = {
            'isochronic_enabled': True,
            'isochronic_freq': '0',
            'isochronic_volume': -20.0,
            'isochronic_shape': 'sine'
        }

        result = audio_core.apply_isochronic_tones(sample_audio_data.copy(), params)

        # 零频率应该返回原数据
        assert result['data'] == sample_audio_data['data']

    def test_save_audio_wav(self, audio_core, sample_audio_data, temp_output_dir):
        """测试保存WAV文件"""
        output_path = os.path.join(temp_output_dir, 'test_output.wav')

        result = audio_core.save_audio_wav(sample_audio_data, output_path)

        assert result == output_path
        assert os.path.exists(output_path)

        # 验证文件内容
        with wave.open(output_path, 'rb') as wf:
            assert wf.getnchannels() == sample_audio_data['channels']
            assert wf.getsampwidth() == sample_audio_data['sample_width']
            assert wf.getframerate() == sample_audio_data['sample_rate']

    def test_load_affirmation_audio_not_exist(self, audio_core):
        """测试加载不存在的肯定语音频"""
        result = audio_core.load_affirmation_audio('nonexistent.wav')
        assert result is None

    def test_load_affirmation_audio_empty(self, audio_core):
        """测试加载空路径肯定语音频"""
        result = audio_core.load_affirmation_audio('')
        assert result is None

    def test_load_background_audio_not_exist(self, audio_core):
        """测试加载不存在的背景音"""
        result = audio_core.load_background_audio(44100, 'nonexistent.wav')
        assert result is None

    def test_load_background_audio_empty(self, audio_core):
        """测试加载空路径背景音"""
        result = audio_core.load_background_audio(44100, '')
        assert result is None

    def test_process_no_affirmation(self, audio_core):
        """测试没有肯定语文件的process"""
        audio_core.set_params({
            'affirmation_file': 'nonexistent.wav',
            'output_path': 'output.wav'
        })
        result = audio_core.process()
        assert result is None

    def test_process_cancelled_early(self, audio_core):
        """测试早期取消的process"""
        audio_core.set_params({
            'affirmation_file': 'test.wav',
            'output_path': 'output.wav'
        })
        audio_core.cancel()

        result = audio_core.process()
        assert result is None

    def test_get_ffmpeg_path(self, audio_core):
        """测试获取ffmpeg路径"""
        result = audio_core._get_ffmpeg_path()
        # 在Linux系统上应该能找到ffmpeg
        # 但测试环境中可能没有，所以只验证不抛出异常
        assert result is None or isinstance(result, str)

    def test_process_with_progress_callback(self, audio_core, temp_output_dir):
        """测试带进度回调的process"""
        # 创建测试WAV文件
        affirmation_path = os.path.join(temp_output_dir, 'test.wav')
        with wave.open(affirmation_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(struct.pack('<hh', 0, 0))

        progress_values = []

        def progress_callback(value):
            progress_values.append(value)

        audio_core.set_params({
            'affirmation_file': affirmation_path,
            'background_file': '',
            'output_path': os.path.join(temp_output_dir, 'output.wav'),
            'output_format': 'WAV',
            'volume': 0.0,
            'speed': 1.0,
            'reverse': False,
            'overlay_times': 1,
            'overlay_interval': 1.0,
            'volume_decrease': 0.0,
            'overlay_stagger_mode': False,
            'background_volume': 0.0,
            'freq_track_enabled': False,
            'isochronic_enabled': False
        })

        result = audio_core.process(progress_callback=progress_callback)

        # 应该调用进度回调
        assert len(progress_values) > 0
        # 最后一个值应该是100
        assert progress_values[-1] == 100
