"""
DecompileCore 单元测试
"""
import pytest
import sys
import os
import tempfile
import wave
import struct
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Src'))

from Processors.DecompileCore import DecompileCore


class TestDecompileCore:
    """DecompileCore 测试类"""

    @pytest.fixture
    def decompile_core(self):
        """创建 DecompileCore 实例"""
        return DecompileCore()

    @pytest.fixture
    def sample_params(self):
        """示例参数"""
        return {
            'input_file': 'test.wav',
            'output_file': 'output.wav',
            'volume': 23.0,
            'speed': 1.0,
            'reverse': False,
            'frequency_mode': ''
        }

    @pytest.fixture
    def sample_audio_info(self):
        """示例音频数据"""
        # 生成1秒的正弦波测试数据
        sample_rate = 44100
        duration = 1.0
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

    def test_init(self, decompile_core):
        """测试初始化"""
        assert decompile_core is not None
        assert decompile_core.params == {}
        assert decompile_core.is_cancelled is False
        assert decompile_core.preview_audio_data is None

    def test_set_params(self, decompile_core, sample_params):
        """测试设置参数"""
        decompile_core.set_params(sample_params)
        assert decompile_core.params == sample_params

    def test_cancel(self, decompile_core):
        """测试取消功能"""
        assert decompile_core.check_cancelled() is False
        decompile_core.cancel()
        assert decompile_core.check_cancelled() is True

    def test_apply_volume(self, decompile_core):
        """测试音量调整"""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        volume_db = 6.0  # 约2倍增益
        result = decompile_core._apply_volume(data, volume_db)

        # 验证结果长度相同
        assert len(result) == len(data)
        # 验证音量增加
        assert result[0] > data[0]

    def test_apply_volume_zero(self, decompile_core):
        """测试音量为0时不改变数据"""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = decompile_core._apply_volume(data, 0.0)
        assert result == data

    def test_apply_speed(self, decompile_core):
        """测试速度调整"""
        data = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
        speed = 2.0
        result = decompile_core._apply_speed(data, speed)

        # 速度2倍，长度应该减半
        assert len(result) == int(len(data) / speed)

    def test_apply_speed_same(self, decompile_core):
        """测试速度为1时不改变数据"""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = decompile_core._apply_speed(data, 1.0)
        assert result == data

    def test_apply_speed_invalid(self, decompile_core):
        """测试无效速度值"""
        data = [0.1, 0.2, 0.3]
        result = decompile_core._apply_speed(data, 0.0)
        assert result == data

        result = decompile_core._apply_speed(data, -1.0)
        assert result == data

    def test_apply_reverse(self, decompile_core):
        """测试倒放"""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = decompile_core._apply_reverse(data)

        # 验证数据被反转
        assert result == [0.5, 0.4, 0.3, 0.2, 0.1]

    def test_wav_to_array_8bit(self, decompile_core):
        """测试8位WAV数据转换"""
        # 8-bit unsigned: 128 is center (0)
        raw_data = bytes([128, 200, 56, 255, 0])
        result = decompile_core._wav_to_array(raw_data, 1, 1)

        assert len(result) == 5
        # 128 -> 0, 200 -> 72/128, 56 -> -72/128
        assert abs(result[0]) < 0.01  # 接近0
        assert result[1] > 0  # 正值
        assert result[2] < 0  # 负值

    def test_wav_to_array_16bit(self, decompile_core):
        """测试16位WAV数据转换"""
        # 16-bit signed
        raw_data = struct.pack('<hhhhh', 0, 16384, -16384, 32767, -32768)
        result = decompile_core._wav_to_array(raw_data, 2, 1)

        assert len(result) == 5
        assert abs(result[0]) < 0.01  # 0
        assert result[1] > 0  # 正值
        assert result[2] < 0  # 负值

    def test_wav_to_array_stereo(self, decompile_core):
        """测试立体声WAV数据转换"""
        # Stereo 16-bit: L0, R0, L1, R1, ...
        raw_data = struct.pack('<hhhh', 10000, 10000, -10000, -10000)
        result = decompile_core._wav_to_array(raw_data, 2, 2)

        # 立体声应该取平均值
        assert len(result) == 2

    def test_array_to_wav_8bit(self, decompile_core):
        """测试8位WAV数据生成"""
        data = [0.0, 0.5, -0.5, 1.0, -1.0]
        result = decompile_core._array_to_wav(data, 1)

        assert isinstance(result, bytes)
        assert len(result) == 5
        # 0.0 -> 128, 0.5 -> ~191, -0.5 -> ~64
        assert result[0] == 128

    def test_array_to_wav_16bit(self, decompile_core):
        """测试16位WAV数据生成"""
        data = [0.0, 0.5, -0.5]
        result = decompile_core._array_to_wav(data, 2)

        assert isinstance(result, bytes)
        assert len(result) == 6  # 3 samples * 2 bytes

    def test_array_to_wav_clipping(self, decompile_core):
        """测试WAV数据裁剪"""
        data = [2.0, -2.0, 1.5, -1.5]  # 超出范围的数据
        result = decompile_core._array_to_wav(data, 2)

        # 应该被裁剪到有效范围
        assert isinstance(result, bytes)

    def test_decompile_none_audio(self, decompile_core, sample_params):
        """测试反编译None音频"""
        result = decompile_core.decompile(None, sample_params)
        assert result is None

    def test_decompile_basic(self, decompile_core, sample_audio_info, sample_params):
        """测试基本反编译流程"""
        result = decompile_core.decompile(sample_audio_info, sample_params)

        assert result is not None
        assert 'data' in result
        assert 'sample_rate' in result
        assert 'channels' in result
        assert 'sample_width' in result

    def test_decompile_with_reverse(self, decompile_core, sample_audio_info):
        """测试带倒放的反编译"""
        params = {
            'reverse': True,
            'speed': 1.0,
            'volume': 0.0,
            'frequency_mode': ''
        }

        original_first = sample_audio_info['data'][0]
        result = decompile_core.decompile(sample_audio_info, params)

        # 倒放后，原第一个值应该变成最后一个
        assert result['data'][-1] == pytest.approx(original_first, rel=1e-3)

    def test_decompile_with_speed(self, decompile_core, sample_audio_info):
        """测试带速度调整的反编译"""
        params = {
            'reverse': False,
            'speed': 2.0,
            'volume': 0.0,
            'frequency_mode': ''
        }

        original_length = len(sample_audio_info['data'])
        result = decompile_core.decompile(sample_audio_info, params)

        # 速度2倍，反编译时取倒数(0.5倍)，长度应该翻倍
        expected_length = int(original_length / 0.5)
        assert len(result['data']) == expected_length

    def test_decompile_with_volume(self, decompile_core, sample_audio_info):
        """测试带音量调整的反编译"""
        params = {
            'reverse': False,
            'speed': 1.0,
            'volume': 6.0,
            'frequency_mode': ''
        }

        original_max = max(abs(x) for x in sample_audio_info['data'])
        result = decompile_core.decompile(sample_audio_info, params)
        result_max = max(abs(x) for x in result['data'])

        # 音量增加后，最大值应该变大
        assert result_max > original_max

    def test_generate_preview(self, decompile_core, sample_audio_info, sample_params):
        """测试生成预览"""
        result = decompile_core.generate_preview(sample_audio_info, sample_params)

        assert result is not None
        assert 'data' in result
        # 预览应该是30秒的数据
        expected_samples = min(30 * sample_audio_info['sample_rate'],
                               len(sample_audio_info['data']))
        assert len(result['data']) <= expected_samples

    def test_get_preview_audio_data(self, decompile_core, sample_audio_info, sample_params):
        """测试获取预览音频数据"""
        # 先生成预览
        decompile_core.generate_preview(sample_audio_info, sample_params)

        # 获取预览数据
        preview = decompile_core.get_preview_audio_data()
        assert preview is not None
        assert 'data' in preview

    def test_save_audio(self, decompile_core, sample_audio_info, temp_output_dir):
        """测试保存音频"""
        output_path = os.path.join(temp_output_dir, 'test_output.wav')

        result = decompile_core.save_audio(sample_audio_info, output_path)

        assert result is True
        assert os.path.exists(output_path)

        # 验证文件内容
        with wave.open(output_path, 'rb') as wf:
            assert wf.getnchannels() == sample_audio_info['channels']
            assert wf.getsampwidth() == sample_audio_info['sample_width']
            assert wf.getframerate() == sample_audio_info['sample_rate']

    def test_save_audio_invalid(self, decompile_core, temp_output_dir):
        """测试保存无效音频"""
        output_path = os.path.join(temp_output_dir, 'test_output.wav')

        # 测试None数据
        result = decompile_core.save_audio(None, output_path)
        assert result is False

        # 测试空路径
        result = decompile_core.save_audio({'data': [0.1]}, '')
        assert result is False

    def test_load_audio_not_exist(self, decompile_core):
        """测试加载不存在的音频"""
        result = decompile_core.load_audio('nonexistent.wav')
        assert result is None

    def test_load_audio_empty_path(self, decompile_core):
        """测试加载空路径"""
        result = decompile_core.load_audio('')
        assert result is None

    def test_process_no_input_file(self, decompile_core):
        """测试没有输入文件的process"""
        decompile_core.set_params({'input_file': ''})
        result = decompile_core.process()
        assert result is None

    def test_apply_frequency_filter_ug(self, decompile_core, sample_audio_info):
        """测试UG频率滤波"""
        data = sample_audio_info['data'][:1000]  # 使用较短数据
        sample_rate = sample_audio_info['sample_rate']

        result = decompile_core._apply_frequency_filter(data, sample_rate, 'ug')

        assert len(result) == len(data)

    def test_apply_frequency_filter_traditional(self, decompile_core, sample_audio_info):
        """测试传统频率滤波"""
        data = sample_audio_info['data'][:1000]
        sample_rate = sample_audio_info['sample_rate']

        result = decompile_core._apply_frequency_filter(data, sample_rate, 'traditional')

        assert len(result) == len(data)

    def test_apply_frequency_filter_unknown(self, decompile_core, sample_audio_info):
        """测试未知频率模式"""
        data = sample_audio_info['data'][:100]
        sample_rate = sample_audio_info['sample_rate']

        result = decompile_core._apply_frequency_filter(data, sample_rate, 'unknown')

        # 未知模式应该返回原数据
        assert result == data

    def test_remove_ug_frequency(self, decompile_core, sample_audio_info):
        """测试移除UG频率"""
        data = sample_audio_info['data'][:1000]
        sample_rate = sample_audio_info['sample_rate']

        result = decompile_core._remove_ug_frequency(data, sample_rate)

        assert len(result) == len(data)

    def test_remove_traditional_frequency(self, decompile_core, sample_audio_info):
        """测试移除传统频率"""
        data = sample_audio_info['data'][:1000]
        sample_rate = sample_audio_info['sample_rate']

        result = decompile_core._remove_traditional_frequency(data, sample_rate)

        assert len(result) == len(data)
