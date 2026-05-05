"""
音频反编译核心模块 - 不依赖 PyQt5
可以被 GUI 和 CLI 共同使用
用于反编译处理后的音频，还原肯定语
"""

import wave
import os
import struct
import math
import subprocess
import tempfile
from loguru import logger

class DecompileCore:
    """音频反编译核心类 - 纯逻辑，无 GUI 依赖"""

    def __init__(self, params=None):
        self.params = params or {}
        self.is_cancelled = False
        self.preview_audio_data = None  # 存储预览音频数据
        logger.debug(f"DecompileCore初始化 - 参数: {params}")

    def set_params(self, params):
        """设置参数"""
        logger.debug(f"DecompileCore.set_params - 设置参数: {params}")
        self.params = params

    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
        logger.info("反编译处理已取消")

    def check_cancelled(self):
        """检查是否已取消"""
        return self.is_cancelled

    def _get_ffmpeg_path(self):
        """查找 ffmpeg 可执行文件路径"""
        import sys

        # 可能的 ffmpeg 可执行文件名
        ffmpeg_names = ['ffmpeg.exe', 'ffmpeg'] if sys.platform == 'win32' else ['ffmpeg']

        # 检查系统 PATH
        for name in ffmpeg_names:
            try:
                result = subprocess.run(['where', name] if sys.platform == 'win32' else ['which', name],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    ffmpeg_path = result.stdout.strip().split('\n')[0].strip()
                    if ffmpeg_path:
                        logger.debug(f"找到 ffmpeg (系统 PATH): {ffmpeg_path}")
                        return ffmpeg_path
            except Exception:
                pass

        # 尝试直接使用 ffmpeg（如果在 PATH 中）
        for name in ffmpeg_names:
            try:
                result = subprocess.run([name, '-version'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.debug(f"找到 ffmpeg (直接调用): {name}")
                    return name
            except Exception:
                pass

        logger.warning("未找到 ffmpeg 可执行文件")
        return None

    def _wav_to_array(self, raw_data, sample_width, channels):
        """将WAV原始数据转换为列表"""
        audio_data = []

        if sample_width == 1:  # 8-bit unsigned
            for i in range(0, len(raw_data), channels):
                if channels == 1:
                    val = raw_data[i] - 128
                    audio_data.append(val / 128.0)
                else:
                    avg = sum(raw_data[i + j] - 128 for j in range(channels)) / channels
                    audio_data.append(avg / 128.0)

        elif sample_width == 2:  # 16-bit signed
            fmt = '<h'
            for i in range(0, len(raw_data), sample_width * channels):
                if channels == 1:
                    val = struct.unpack(fmt, raw_data[i:i+sample_width])[0]
                    audio_data.append(val / 32768.0)
                else:
                    samples = [struct.unpack(fmt, raw_data[i + j*sample_width:i + (j+1)*sample_width])[0]
                              for j in range(channels)]
                    avg = sum(samples) / channels
                    audio_data.append(avg / 32768.0)

        elif sample_width == 3:  # 24-bit
            for i in range(0, len(raw_data), 3 * channels):
                if channels == 1:
                    sample = raw_data[i:i+3]
                    val = int.from_bytes(sample, byteorder='little', signed=True)
                    audio_data.append(val / 8388608.0)
                else:
                    samples = []
                    for j in range(channels):
                        sample = raw_data[i + j*3:i + (j+1)*3]
                        val = int.from_bytes(sample, byteorder='little', signed=True)
                        samples.append(val)
                    avg = sum(samples) / channels
                    audio_data.append(avg / 8388608.0)

        elif sample_width == 4:  # 32-bit
            fmt = '<i'
            for i in range(0, len(raw_data), 4 * channels):
                if channels == 1:
                    val = struct.unpack(fmt, raw_data[i:i+4])[0]
                    audio_data.append(val / 2147483648.0)
                else:
                    samples = [struct.unpack(fmt, raw_data[i + j*4:i + (j+1)*4])[0]
                              for j in range(channels)]
                    avg = sum(samples) / channels
                    audio_data.append(avg / 2147483648.0)

        return audio_data

    def _array_to_wav(self, audio_data, sample_width):
        """将列表转换回WAV原始数据"""
        raw_data = bytearray()

        if sample_width == 1:  # 8-bit unsigned
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 127 + 128)
                raw_data.append(val & 0xFF)

        elif sample_width == 2:  # 16-bit signed
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 32767)
                raw_data.extend(struct.pack('<h', val))

        elif sample_width == 3:  # 24-bit
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 8388607)
                raw_data.extend(val.to_bytes(3, byteorder='little', signed=True))

        elif sample_width == 4:  # 32-bit
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 2147483647)
                raw_data.extend(struct.pack('<i', val))

        return bytes(raw_data)

    def load_audio(self, file_path):
        """加载音频文件"""
        try:
            if not file_path or not os.path.exists(file_path):
                logger.error(f"音频文件不存在: {file_path}")
                return None

            logger.info(f"加载音频: {file_path}")
            file_path = os.path.abspath(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()

            # 如果是WAV格式，直接使用wave模块加载
            if file_ext == '.wav':
                with wave.open(file_path, 'rb') as wf:
                    n_channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    framerate = wf.getframerate()
                    n_frames = wf.getnframes()
                    logger.debug(f"WAV文件信息 - 通道数: {n_channels}, 采样宽度: {sample_width}, 采样率: {framerate}, 帧数: {n_frames}")
                    raw_data = wf.readframes(n_frames)
                audio_data = self._wav_to_array(raw_data, sample_width, n_channels)
            else:
                # 对于非WAV格式，使用ffmpeg转换为临时WAV文件
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    temp_wav_path = temp_wav.name

                try:
                    ffmpeg_exe = self._get_ffmpeg_path()
                    if not ffmpeg_exe:
                        logger.error("未找到 ffmpeg 可执行文件")
                        return None

                    ffmpeg_cmd = [
                        ffmpeg_exe, '-y', '-i', file_path,
                        '-codec:a', 'pcm_s16le', temp_wav_path
                    ]

                    logger.debug(f"执行 FFmpeg 命令: {' '.join(ffmpeg_cmd)}")
                    result = subprocess.run(
                        ffmpeg_cmd, capture_output=True, text=True, timeout=60
                    )

                    if result.returncode != 0:
                        logger.error(f"FFmpeg转换失败: {result.stderr}")
                        return None

                    with wave.open(temp_wav_path, 'rb') as wf:
                        n_channels = wf.getnchannels()
                        sample_width = wf.getsampwidth()
                        framerate = wf.getframerate()
                        n_frames = wf.getnframes()
                        raw_data = wf.readframes(n_frames)
                        audio_data = self._wav_to_array(raw_data, sample_width, n_channels)
                finally:
                    if os.path.exists(temp_wav_path):
                        os.remove(temp_wav_path)

            return {
                'data': audio_data,
                'sample_rate': framerate,
                'channels': n_channels,
                'sample_width': sample_width
            }

        except Exception as e:
            logger.error(f"加载音频失败: {e}")
            return None

    def _apply_volume(self, data, volume_db):
        """应用音量调整"""
        if volume_db == 0.0:
            return data
        volume_factor = 10 ** (volume_db / 20.0)
        logger.info(f"应用音量调整: {volume_db}dB")
        return [s * volume_factor for s in data]

    def _apply_speed(self, data, speed):
        """改变音频速度（简单重采样）"""
        if speed <= 0 or speed == 1.0:
            return data

        logger.info(f"应用倍速: {speed}x")
        new_length = int(len(data) / speed)
        result = []

        for i in range(new_length):
            src_idx = i * speed
            idx_low = int(src_idx)
            idx_high = min(idx_low + 1, len(data) - 1)
            frac = src_idx - idx_low
            val = data[idx_low] * (1 - frac) + data[idx_high] * frac
            result.append(val)

        return result

    def _apply_reverse(self, data):
        """倒放音频"""
        logger.info("应用倒放效果")
        return data[::-1]

    def _remove_ug_frequency(self, data, sample_rate):
        """移除UG频率模式（亚超声波：17500-20000Hz），使用带通滤波器"""
        logger.info("移除UG频率模式（亚超声波）")
        # UG频率使用18750Hz载波，我们需要解调
        carrier_freq = 18750
        result = []
        for i, sample in enumerate(data):
            t = i / sample_rate
            carrier = math.sin(2 * math.pi * carrier_freq * t)
            # 解调：乘以载波
            demodulated = sample * carrier
            result.append(demodulated)
        return result

    def _remove_traditional_frequency(self, data, sample_rate):
        """移除传统频率模式（次声波：100-300Hz），使用高通滤波器"""
        logger.info("移除传统频率模式（次声波）")
        # 简单的低通滤波器去除高频，保留人声
        window_size = int(sample_rate / 300)
        if window_size < 2:
            window_size = 2

        filtered = []
        for i in range(len(data)):
            start = max(0, i - window_size // 2)
            end = min(len(data), i + window_size // 2 + 1)
            window = data[start:end]
            filtered.append(sum(window) / len(window))

        return filtered

    def _apply_frequency_filter(self, data, sample_rate, freq_mode):
        """应用频率滤波"""
        if freq_mode == "ug" or freq_mode == "1":
            return self._remove_ug_frequency(data, sample_rate)
        elif freq_mode == "traditional" or freq_mode == "2":
            return self._remove_traditional_frequency(data, sample_rate)
        return data

    def decompile(self, audio_info, params=None):
        """
        反编译音频
        这是编译的逆过程：音量取反、频率还原、速度还原、倒放还原
        """
        if params is None:
            params = self.params

        if not audio_info:
            logger.error("没有音频数据可供反编译")
            return None

        data = audio_info['data'].copy()
        sample_rate = audio_info['sample_rate']
        sample_width = audio_info['sample_width']
        channels = audio_info['channels']

        logger.info("开始反编译音频...")

        # 1. 倒放还原（如果原始音频是倒放的，先还原）
        if params.get('reverse', False):
            data = self._apply_reverse(data)
            if self.check_cancelled():
                return None

        # 2. 速度还原
        speed = params.get('speed', 1.0)
        if speed != 1.0:
            # 反编译时速度取倒数
            data = self._apply_speed(data, 1.0 / speed)
            if self.check_cancelled():
                return None

        # 3. 频率还原
        freq_mode = params.get('frequency_mode', '')
        if freq_mode:
            data = self._apply_frequency_filter(data, sample_rate, freq_mode)
            if self.check_cancelled():
                return None

        # 4. 音量还原（反编译时通常需要增加音量）
        volume_db = params.get('volume', 23.0)
        data = self._apply_volume(data, volume_db)
        if self.check_cancelled():
            return None

        # 防止削波
        max_val = max(abs(s) for s in data) if data else 1.0
        if max_val > 1.0:
            data = [s / max_val for s in data]
            logger.info(f"音频归一化，峰值: {max_val:.2f}")

        logger.info("反编译完成")

        return {
            'data': data,
            'sample_rate': sample_rate,
            'channels': channels,
            'sample_width': sample_width
        }

    def save_audio(self, audio_info, output_path):
        """保存音频到文件"""
        try:
            if not audio_info or not output_path:
                logger.error("无效的音频数据或输出路径")
                return False

            data = audio_info['data']
            sample_rate = audio_info['sample_rate']
            channels = audio_info['channels']
            sample_width = audio_info['sample_width']

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            raw_data = self._array_to_wav(data, sample_width)

            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(sample_rate)
                wf.writeframes(raw_data)

            logger.info(f"音频已保存: {output_path}")
            return True

        except Exception as e:
            logger.error(f"保存音频失败: {e}")
            return False

    def generate_preview(self, audio_info, params=None, progress_callback=None):
        """生成预览音频（前30秒）"""
        if params is None:
            params = self.params

        if not audio_info:
            return None

        # 复制音频数据，只取前30秒
        sample_rate = audio_info['sample_rate']
        preview_duration = 30  # 30秒预览
        preview_samples = min(int(preview_duration * sample_rate), len(audio_info['data']))

        preview_info = {
            'data': audio_info['data'][:preview_samples],
            'sample_rate': sample_rate,
            'channels': audio_info['channels'],
            'sample_width': audio_info['sample_width']
        }

        # 反编译预览数据
        result = self.decompile(preview_info, params)

        if progress_callback:
            progress_callback(100)

        self.preview_audio_data = result
        return result

    def get_preview_audio_data(self):
        """获取预览音频数据"""
        return self.preview_audio_data

    def process(self, progress_callback=None):
        """
        执行完整的反编译处理流程
        用于导出完整音频
        """
        try:
            file_path = self.params.get('input_file')
            if not file_path:
                logger.error("未指定输入文件")
                return None

            # 加载音频
            if progress_callback:
                progress_callback(10)

            audio_info = self.load_audio(file_path)
            if not audio_info:
                return None

            if self.check_cancelled():
                return None

            if progress_callback:
                progress_callback(30)

            # 反编译
            result = self.decompile(audio_info, self.params)

            if self.check_cancelled():
                return None

            if progress_callback:
                progress_callback(80)

            # 保存
            output_path = self.params.get('output_file')
            if output_path and result:
                if self.save_audio(result, output_path):
                    if progress_callback:
                        progress_callback(100)
                    return output_path

            return None

        except Exception as e:
            logger.error(f"反编译处理失败: {e}")
            return None
