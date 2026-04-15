"""
音频处理核心模块 - 不依赖 PyQt5
可以被 GUI 和 CLI 共同使用
"""

import wave
import os
import struct
import math
import subprocess
import tempfile
from loguru import logger


class AudioCore:
    """音频处理核心类 - 纯逻辑，无 GUI 依赖"""

    def __init__(self, params=None):
        self.params = params or {}
        self.is_cancelled = False
        logger.debug(f"AudioCore初始化 - 参数: {params}")
        if params:
            affirmation_file = params.get('affirmation_file')
            background_file = params.get('background_file')
            output_path = params.get('output_path')
            logger.debug(f"AudioCore初始化文件路径 - affirmation_file: {affirmation_file}, background_file: {background_file}, output_path: {output_path}")
            if affirmation_file:
                logger.debug(f"肯定语文件绝对路径: {os.path.abspath(affirmation_file)}, 是否存在: {os.path.exists(affirmation_file)}")
            if background_file:
                logger.debug(f"背景音文件绝对路径: {os.path.abspath(background_file)}, 是否存在: {os.path.exists(background_file)}")
            if output_path:
                output_dir = os.path.dirname(output_path)
                logger.debug(f"输出目录绝对路径: {os.path.abspath(output_dir) if output_dir else 'None'}, 是否存在: {os.path.exists(output_dir) if output_dir else False}")

    def set_params(self, params):
        """设置参数"""
        logger.debug(f"AudioCore.set_params - 设置参数: {params}")
        self.params = params
        affirmation_file = params.get('affirmation_file')
        background_file = params.get('background_file')
        output_path = params.get('output_path')
        logger.debug(f"AudioCore.set_params文件路径 - affirmation_file: {affirmation_file}, background_file: {background_file}, output_path: {output_path}")

    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
        logger.info("音频处理已取消")

    def check_cancelled(self):
        """检查是否已取消"""
        return self.is_cancelled

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

    def _resample_audio(self, data, src_rate, dst_rate):
        """重采样音频数据从源采样率到目标采样率"""
        if src_rate == dst_rate:
            return data

        src_length = len(data)
        dst_length = int(src_length * dst_rate / src_rate)

        result = []
        for i in range(dst_length):
            src_idx = i * src_rate / dst_rate
            idx_low = int(src_idx)
            idx_high = min(idx_low + 1, src_length - 1)
            frac = src_idx - idx_low
            val = data[idx_low] * (1 - frac) + data[idx_high] * frac
            result.append(val)

        return result

    def _change_speed(self, data, speed):
        """改变音频速度（简单重采样）"""
        if speed <= 0:
            return data

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

    def _apply_ug_frequency(self, data, sample_rate):
        """应用UG频率模式（亚超声波：17500-20000Hz）"""
        carrier_freq = 18750
        result = []
        for i, sample in enumerate(data):
            t = i / sample_rate
            carrier = math.sin(2 * math.pi * carrier_freq * t)
            modulated = sample * carrier
            result.append(modulated)
        return result

    def _apply_traditional_frequency(self, data, sample_rate):
        """应用传统频率模式（次声波：100-300Hz）"""
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

    def load_affirmation_audio(self, file_path=None):
        """加载肯定语音频文件"""
        try:
            if file_path is None:
                file_path = self.params.get('affirmation_file')

            logger.info(f"加载肯定语音频: {file_path}")
            logger.debug(f"肯定语文件路径详情: file_path={file_path}")
            if file_path:
                logger.debug(f"肯定语文件绝对路径: {os.path.abspath(file_path)}")
                logger.debug(f"肯定语文件是否存在: {os.path.exists(file_path)}")
                if os.path.exists(file_path):
                    logger.debug(f"肯定语文件大小: {os.path.getsize(file_path)} bytes")

            if not file_path or not os.path.exists(file_path):
                logger.error(f"肯定语音频文件不存在: {file_path}")
                if file_path:
                    logger.debug(f"文件绝对路径: {os.path.abspath(file_path)}")
                return None

            logger.debug(f"开始读取WAV文件: {file_path}")
            with wave.open(file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                logger.debug(f"WAV文件信息 - 通道数: {n_channels}, 采样宽度: {sample_width}, 采样率: {framerate}, 帧数: {n_frames}")
                raw_data = wf.readframes(n_frames)
                logger.debug(f"WAV原始数据大小: {len(raw_data)} bytes")
                audio_data = self._wav_to_array(raw_data, sample_width, n_channels)
                logger.debug(f"转换后的音频数据长度: {len(audio_data)} samples")

                return {
                    'data': audio_data,
                    'sample_rate': framerate,
                    'channels': n_channels,
                    'sample_width': sample_width
                }

        except Exception as e:
            logger.error(f"加载肯定语音频失败: {e}")
            return None

    def process_affirmation_effects(self, audio_data, params=None):
        """处理肯定语效果：音量、频率、倍速、倒放"""
        if params is None:
            params = self.params

        data = audio_data['data']
        sample_rate = audio_data['sample_rate']

        # 1. 应用倍速
        speed = params.get('speed', 1.0)
        if speed != 1.0:
            logger.info(f"应用倍速: {speed}x")
            data = self._change_speed(data, speed)
            sample_rate = int(sample_rate * speed)

        # 2. 应用倒放
        if params.get('reverse', False):
            logger.info("应用倒放效果")
            data = data[::-1]

        # 3. 应用频率变换
        freq_mode = params.get('frequency_mode', 0)
        if freq_mode == 1:
            logger.info("应用UG频率模式（亚超声波）")
            data = self._apply_ug_frequency(data, sample_rate)
        elif freq_mode == 2:
            logger.info("应用传统频率模式（次声波）")
            data = self._apply_traditional_frequency(data, sample_rate)

        # 4. 应用音量调整
        volume_db = params.get('volume', -23.0)
        if volume_db != 0.0:
            volume_factor = 10 ** (volume_db / 20.0)
            logger.info(f"应用音量调整: {volume_db}dB")
            data = [s * volume_factor for s in data]

        audio_data['data'] = data
        audio_data['sample_rate'] = sample_rate
        return audio_data

    def apply_overlay(self, audio_data, params=None):
        """应用叠加效果"""
        if params is None:
            params = self.params

        overlay_times = params.get('overlay_times', 1)
        overlay_interval = params.get('overlay_interval', 1.0)
        volume_decrease = params.get('volume_decrease', 0.0)

        if overlay_times <= 1:
            return audio_data

        logger.info(f"应用叠加效果: {overlay_times}次, 间隔{overlay_interval}s")

        data = audio_data['data']
        sample_rate = audio_data['sample_rate']
        interval_samples = int(overlay_interval * sample_rate)
        final_length = len(data) + (overlay_times - 1) * interval_samples
        result = [0.0] * final_length

        for i in range(overlay_times):
            current_volume_db = -i * volume_decrease
            volume_factor = 10 ** (current_volume_db / 20.0)
            offset = i * interval_samples
            for j, sample in enumerate(data):
                if offset + j < final_length:
                    result[offset + j] += sample * volume_factor

        max_val = max(abs(s) for s in result) if result else 1.0
        if max_val > 1.0:
            result = [s / max_val for s in result]

        audio_data['data'] = result
        return audio_data

    def load_background_audio(self, target_sample_rate, file_path=None, bg_volume_db=None):
        """加载并处理背景音乐"""
        if file_path is None:
            file_path = self.params.get('background_file', '')
        if bg_volume_db is None:
            bg_volume_db = self.params.get('background_volume', 0.0)

        if not file_path or not os.path.exists(file_path):
            logger.debug(f"背景音文件不存在或路径为空: {file_path}")
            return None

        try:
            logger.info(f"加载背景音乐: {file_path}")
            logger.debug(f"背景音文件路径详情: file_path={file_path}, target_sample_rate={target_sample_rate}")
            logger.debug(f"背景音文件绝对路径: {os.path.abspath(file_path)}")
            logger.debug(f"背景音文件大小: {os.path.getsize(file_path)} bytes")

            with wave.open(file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                logger.debug(f"背景音WAV文件信息 - 通道数: {n_channels}, 采样宽度: {sample_width}, 采样率: {framerate}, 帧数: {n_frames}")
                raw_data = wf.readframes(n_frames)
                logger.debug(f"背景音WAV原始数据大小: {len(raw_data)} bytes")
                audio_data = self._wav_to_array(raw_data, sample_width, n_channels)
                logger.debug(f"背景音转换后的音频数据长度: {len(audio_data)} samples")

                volume_factor = 10 ** (bg_volume_db / 20.0)
                logger.debug(f"背景音音量调整: {bg_volume_db}dB, 音量因子: {volume_factor}")
                audio_data = [s * volume_factor for s in audio_data]

                if framerate != target_sample_rate:
                    logger.debug(f"背景音需要重采样: {framerate} -> {target_sample_rate}")
                    audio_data = self._resample_audio(audio_data, framerate, target_sample_rate)
                    logger.debug(f"背景音重采样后数据长度: {len(audio_data)} samples")

                return {
                    'data': audio_data,
                    'sample_rate': target_sample_rate,
                    'channels': 1,
                    'sample_width': sample_width
                }

        except Exception as e:
            logger.error(f"加载背景音乐失败: {e}")
            return None

    def merge_audio(self, affirmation_data, background_data, ensure_integrity=None):
        """合并肯定语和背景音乐"""
        if ensure_integrity is None:
            ensure_integrity = self.params.get('ensure_integrity', False)

        logger.info("合并音频")
        logger.debug(f"合并音频参数 - ensure_integrity={ensure_integrity}")

        aff_data = affirmation_data['data']
        logger.debug(f"肯定语数据长度: {len(aff_data)} samples")

        if background_data is None:
            logger.debug("背景音数据为空，返回肯定语数据")
            return affirmation_data

        bg_data = background_data['data']
        bg_length = len(bg_data)
        aff_length = len(aff_data)
        logger.debug(f"背景音数据长度: {bg_length} samples, 肯定语数据长度: {aff_length} samples")
        result = []

        if ensure_integrity:
            full_cycles = bg_length // aff_length
            remaining_samples = bg_length % aff_length

            logger.info(f"确保完整性模式: 完整循环次数={full_cycles}")
            logger.debug(f"确保完整性模式详情 - full_cycles={full_cycles}, remaining_samples={remaining_samples}")

            for cycle in range(full_cycles):
                for j in range(aff_length):
                    idx = cycle * aff_length + j
                    mixed = aff_data[j] + bg_data[idx]
                    mixed = max(-1.0, min(1.0, mixed))
                    result.append(mixed)

            if remaining_samples > 0:
                for i in range(remaining_samples):
                    idx = full_cycles * aff_length + i
                    mixed = bg_data[idx]
                    mixed = max(-1.0, min(1.0, mixed))
                    result.append(mixed)
        else:
            for i in range(bg_length):
                aff_idx = i % aff_length
                mixed = aff_data[aff_idx] + bg_data[i]
                mixed = max(-1.0, min(1.0, mixed))
                result.append(mixed)

        logger.debug(f"合并完成，结果数据长度: {len(result)} samples")

        return {
            'data': result,
            'sample_rate': affirmation_data['sample_rate'],
            'channels': 1,
            'sample_width': affirmation_data['sample_width']
        }

    def save_audio_wav(self, audio_data, output_path):
        """保存为WAV格式"""
        logger.debug(f"开始保存WAV文件: {output_path}")
        logger.debug(f"输出目录绝对路径: {os.path.abspath(os.path.dirname(output_path))}")

        raw_data = self._array_to_wav(audio_data['data'], audio_data['sample_width'])
        logger.debug(f"WAV原始数据大小: {len(raw_data)} bytes")

        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(audio_data['channels'])
            wf.setsampwidth(audio_data['sample_width'])
            wf.setframerate(audio_data['sample_rate'])
            wf.writeframes(raw_data)

        logger.info(f"WAV音频文件已保存: {output_path}")
        logger.debug(f"WAV文件保存成功，绝对路径: {os.path.abspath(output_path)}, 大小: {os.path.getsize(output_path)} bytes")
        return output_path

    def save_audio_mp3(self, audio_data, output_path, metadata_title='', metadata_author=''):
        """使用FFmpeg保存为MP3格式"""
        logger.debug(f"开始保存MP3文件: {output_path}")
        logger.debug(f"MP3输出目录绝对路径: {os.path.abspath(os.path.dirname(output_path))}")

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        logger.debug(f"临时WAV文件路径: {temp_wav_path}")

        try:
            raw_data = self._array_to_wav(audio_data['data'], audio_data['sample_width'])
            logger.debug(f"临时WAV原始数据大小: {len(raw_data)} bytes")

            with wave.open(temp_wav_path, 'wb') as wf:
                wf.setnchannels(audio_data['channels'])
                wf.setsampwidth(audio_data['sample_width'])
                wf.setframerate(audio_data['sample_rate'])
                wf.writeframes(raw_data)

            logger.debug(f"临时WAV文件已写入: {temp_wav_path}, 大小: {os.path.getsize(temp_wav_path)} bytes")

            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', temp_wav_path,
                '-codec:a', 'libmp3lame', '-q:a', '2'
            ]

            if metadata_title:
                ffmpeg_cmd.extend(['-metadata', f'title={metadata_title}'])
            if metadata_author:
                ffmpeg_cmd.extend(['-metadata', f'artist={metadata_author}'])

            ffmpeg_cmd.append(output_path)

            logger.info(f"转换为MP3: {output_path}")
            logger.debug(f"FFmpeg命令: {' '.join(ffmpeg_cmd)}")

            result = subprocess.run(
                ffmpeg_cmd, capture_output=True, text=True, timeout=120
            )

            logger.debug(f"FFmpeg返回码: {result.returncode}")

            if result.returncode == 0:
                logger.info(f"MP3音频文件已保存: {output_path}")
                if os.path.exists(output_path):
                    logger.debug(f"MP3文件保存成功，绝对路径: {os.path.abspath(output_path)}, 大小: {os.path.getsize(output_path)} bytes")
                return output_path
            else:
                logger.error(f"FFmpeg转换MP3失败: {result.stderr}")
                return None

        finally:
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
                logger.debug(f"临时WAV文件已删除: {temp_wav_path}")

    def write_metadata(self, audio_path, metadata_title='', metadata_author=''):
        """使用FFmpeg写入元数据"""
        try:
            if not metadata_title and not metadata_author:
                logger.debug("无元数据需要写入，跳过")
                return

            logger.debug(f"开始写入元数据 - audio_path: {audio_path}, title: {metadata_title}, author: {metadata_author}")
            logger.debug(f"音频文件绝对路径: {os.path.abspath(audio_path)}, 是否存在: {os.path.exists(audio_path)}")

            metadata_args = []
            if metadata_title:
                metadata_args.extend(['-metadata', f'title={metadata_title}'])
            if metadata_author:
                metadata_args.extend(['-metadata', f'artist={metadata_author}'])

            file_ext = os.path.splitext(audio_path)[1].lower()
            temp_path = audio_path + '.temp' + file_ext
            logger.debug(f"临时文件路径: {temp_path}")

            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', audio_path, '-c', 'copy'
            ] + metadata_args + [temp_path]

            logger.info(f"写入音频元数据: title={metadata_title}, artist={metadata_author}")
            logger.debug(f"FFmpeg元数据命令: {' '.join(ffmpeg_cmd)}")

            result = subprocess.run(
                ffmpeg_cmd, capture_output=True, text=True, timeout=60
            )

            logger.debug(f"FFmpeg元数据写入返回码: {result.returncode}")

            if result.returncode == 0:
                os.replace(temp_path, audio_path)
                logger.info("音频元数据写入成功")
                logger.debug(f"元数据写入后的文件: {audio_path}, 绝对路径: {os.path.abspath(audio_path)}")
            else:
                logger.error(f"FFmpeg元数据写入失败: {result.stderr}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"临时文件已删除: {temp_path}")

        except Exception as e:
            logger.warning(f"写入音频元数据时出错: {e}")

    def process(self, params=None, progress_callback=None):
        """执行完整的处理流程"""
        if params is not None:
            self.params = params
            logger.debug(f"process方法更新参数: {params}")

        try:
            logger.info("开始音频处理")
            logger.debug(f"process方法当前参数 - affirmation_file: {self.params.get('affirmation_file')}, output_path: {self.params.get('output_path')}")

            if progress_callback:
                progress_callback(5)

            if self.check_cancelled():
                return None

            affirmation_data = self.load_affirmation_audio()
            if affirmation_data is None:
                logger.error("加载肯定语音频失败")
                return None
            if progress_callback:
                progress_callback(20)

            if self.check_cancelled():
                return None

            affirmation_data = self.process_affirmation_effects(affirmation_data)
            if progress_callback:
                progress_callback(40)

            if self.check_cancelled():
                return None

            affirmation_data = self.apply_overlay(affirmation_data)
            if progress_callback:
                progress_callback(60)

            if self.check_cancelled():
                return None

            background_data = self.load_background_audio(affirmation_data['sample_rate'])
            if progress_callback:
                progress_callback(75)

            if self.check_cancelled():
                return None

            final_data = self.merge_audio(affirmation_data, background_data)
            if progress_callback:
                progress_callback(90)

            if self.check_cancelled():
                return None

            output_path = self.params.get('output_path')
            output_format = self.params.get('output_format', 'WAV').upper()
            metadata_title = self.params.get('metadata_title', '')
            metadata_author = self.params.get('metadata_author', '')

            logger.debug(f"process方法保存参数 - output_path: {output_path}, output_format: {output_format}")
            logger.debug(f"process方法输出目录: {os.path.abspath(os.path.dirname(output_path)) if output_path else 'None'}")

            if output_format == 'MP3':
                result = self.save_audio_mp3(final_data, output_path, metadata_title, metadata_author)
            else:
                result = self.save_audio_wav(final_data, output_path)
                if result:
                    self.write_metadata(output_path, metadata_title, metadata_author)

            if progress_callback:
                progress_callback(100)

            if result:
                logger.info(f"音频处理完成: {output_path}")
                logger.debug(f"音频处理完成，输出文件绝对路径: {os.path.abspath(output_path)}")
                return output_path
            else:
                logger.error("保存音频文件失败")
                return None

        except Exception as e:
            logger.error(f"音频处理出错: {e}")
            return None
