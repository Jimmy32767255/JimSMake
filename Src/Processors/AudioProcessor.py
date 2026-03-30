from PyQt5.QtCore import QThread, pyqtSignal
import wave
import os
import struct
import math
from loguru import logger


class AudioProcessor(QThread):
    """音频处理线程 - 处理肯定语和背景音乐的合并"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_cancelled = False

    def run(self):
        """执行音频处理"""
        try:
            logger.info("开始音频处理线程")
            self.progress_updated.emit(5)

            # 检查是否取消
            if self.is_cancelled:
                return

            # 1. 加载肯定语音频
            affirmation_data = self.load_affirmation_audio()
            if affirmation_data is None:
                self.processing_error.emit(self.tr("加载肯定语音频失败"))
                return
            self.progress_updated.emit(20)

            # 检查是否取消
            if self.is_cancelled:
                return

            # 2. 处理肯定语效果（音量、频率、倍速、倒放）
            affirmation_data = self.process_affirmation_effects(affirmation_data)
            self.progress_updated.emit(40)

            # 检查是否取消
            if self.is_cancelled:
                return

            # 3. 应用叠加效果
            affirmation_data = self.apply_overlay(affirmation_data)
            self.progress_updated.emit(60)

            # 检查是否取消
            if self.is_cancelled:
                return

            # 4. 加载并处理背景音乐
            background_data = self.load_background_audio(affirmation_data['sample_rate'])
            self.progress_updated.emit(75)

            # 检查是否取消
            if self.is_cancelled:
                return

            # 5. 合并音频
            final_data = self.merge_audio(affirmation_data, background_data)
            self.progress_updated.emit(90)

            # 检查是否取消
            if self.is_cancelled:
                return

            # 6. 保存输出文件
            output_path = self.save_audio(final_data)
            self.progress_updated.emit(100)

            if output_path:
                self.processing_finished.emit(output_path)
                logger.info(f"音频处理完成，输出: {output_path}")
            else:
                self.processing_error.emit(self.tr("保存音频文件失败"))

        except Exception as e:
            logger.error(f"音频处理出错: {e}")
            self.processing_error.emit(str(e))

    def load_affirmation_audio(self):
        """加载肯定语音频文件"""
        try:
            file_path = self.params['affirmation_file']
            logger.info(f"加载肯定语音频: {file_path}")

            if not os.path.exists(file_path):
                logger.error(f"肯定语音频文件不存在: {file_path}")
                return None

            # 读取WAV文件
            with wave.open(file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()

                # 读取音频数据
                raw_data = wf.readframes(n_frames)

                # 转换为numpy数组进行后续处理
                audio_data = self._wav_to_array(raw_data, sample_width, n_channels)

                return {
                    'data': audio_data,
                    'sample_rate': framerate,
                    'channels': n_channels,
                    'sample_width': sample_width
                }

        except Exception as e:
            logger.error(f"加载肯定语音频失败: {e}")
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
                    # 多通道，取平均值转为单声道
                    avg = sum(raw_data[i + j] - 128 for j in range(channels)) / channels
                    audio_data.append(avg / 128.0)

        elif sample_width == 2:  # 16-bit signed
            fmt = '<h'  # little-endian short
            for i in range(0, len(raw_data), sample_width * channels):
                if channels == 1:
                    val = struct.unpack(fmt, raw_data[i:i+sample_width])[0]
                    audio_data.append(val / 32768.0)
                else:
                    # 多通道，取平均值转为单声道
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
            fmt = '<i'  # little-endian int
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

        # 计算重采样后的长度
        src_length = len(data)
        dst_length = int(src_length * dst_rate / src_rate)

        result = []
        for i in range(dst_length):
            src_idx = i * src_rate / dst_rate
            idx_low = int(src_idx)
            idx_high = min(idx_low + 1, src_length - 1)
            frac = src_idx - idx_low

            # 线性插值
            val = data[idx_low] * (1 - frac) + data[idx_high] * frac
            result.append(val)

        return result

    def process_affirmation_effects(self, audio_data):
        """处理肯定语效果：音量、频率、倍速、倒放"""
        data = audio_data['data']
        sample_rate = audio_data['sample_rate']

        # 1. 应用倍速（时间拉伸/压缩）
        speed = self.params.get('speed', 1.0)
        if speed != 1.0:
            logger.info(f"应用倍速: {speed}x")
            data = self._change_speed(data, speed)
            sample_rate = int(sample_rate * speed)

        # 2. 应用倒放
        if self.params.get('reverse', False):
            logger.info("应用倒放效果")
            data = data[::-1]

        # 3. 应用频率变换
        freq_mode = self.params.get('frequency_mode', 0)
        if freq_mode == 1:  # UG（亚超声波）- 提升到17500-20000Hz范围
            logger.info("应用UG频率模式（亚超声波）")
            data = self._apply_ug_frequency(data, sample_rate)
        elif freq_mode == 2:  # 传统（次声波）- 降低到100-300Hz范围
            logger.info("应用传统频率模式（次声波）")
            data = self._apply_traditional_frequency(data, sample_rate)

        # 4. 应用音量调整
        volume_db = self.params.get('volume', 0.0)
        if volume_db != 0.0:
            volume_factor = 10 ** (volume_db / 20.0)
            logger.info(f"应用音量调整: {volume_db}dB (因子: {volume_factor})")
            data = [s * volume_factor for s in data]

        audio_data['data'] = data
        audio_data['sample_rate'] = sample_rate
        return audio_data

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

            # 线性插值
            val = data[idx_low] * (1 - frac) + data[idx_high] * frac
            result.append(val)

        return result

    def _apply_ug_frequency(self, data, sample_rate):
        """应用UG频率模式（亚超声波：17500-20000Hz）"""
        # 使用简单的AM调制将音频搬移到高频
        # 载波频率：18750Hz（在17500-20000Hz范围内）
        carrier_freq = 18750

        # 生成载波
        result = []
        for i, sample in enumerate(data):
            t = i / sample_rate
            carrier = math.sin(2 * math.pi * carrier_freq * t)
            # AM调制
            modulated = sample * carrier
            result.append(modulated)

        return result

    def _apply_traditional_frequency(self, data, sample_rate):
        """应用传统频率模式（次声波：100-300Hz）"""
        # 使用低通滤波器效果（简单的平均滤波）
        # 以及降采样来模拟低频效果

        # 先进行低通滤波（移动平均）
        window_size = int(sample_rate / 300)  # 截止频率约300Hz
        if window_size < 2:
            window_size = 2

        filtered = []
        for i in range(len(data)):
            start = max(0, i - window_size // 2)
            end = min(len(data), i + window_size // 2 + 1)
            window = data[start:end]
            filtered.append(sum(window) / len(window))

        return filtered

    def apply_overlay(self, audio_data):
        """应用叠加效果"""
        overlay_times = self.params.get('overlay_times', 1)
        overlay_interval = self.params.get('overlay_interval', 1.0)
        volume_decrease = self.params.get('volume_decrease', 0.0)

        if overlay_times <= 1:
            return audio_data

        logger.info(f"应用叠加效果: {overlay_times}次, 间隔{overlay_interval}s, 音量递减{volume_decrease}dB")

        data = audio_data['data']
        sample_rate = audio_data['sample_rate']

        # 计算每个叠加的样本偏移
        interval_samples = int(overlay_interval * sample_rate)

        # 计算最终音频长度
        final_length = len(data) + (overlay_times - 1) * interval_samples
        result = [0.0] * final_length

        # 叠加音频
        for i in range(overlay_times):
            # 计算当前叠加的音量
            current_volume_db = -i * volume_decrease
            volume_factor = 10 ** (current_volume_db / 20.0)

            offset = i * interval_samples
            for j, sample in enumerate(data):
                if offset + j < final_length:
                    result[offset + j] += sample * volume_factor

        # 归一化，防止削波
        max_val = max(abs(s) for s in result) if result else 1.0
        if max_val > 1.0:
            result = [s / max_val for s in result]

        audio_data['data'] = result
        return audio_data

    def load_background_audio(self, target_sample_rate):
        """加载并处理背景音乐，保持原始时长"""
        file_path = self.params.get('background_file', '')

        if not file_path or not os.path.exists(file_path):
            # 如果没有背景音乐，返回None表示不需要背景音乐
            return None

        try:
            logger.info(f"加载背景音乐: {file_path}")

            with wave.open(file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()

                raw_data = wf.readframes(n_frames)
                audio_data = self._wav_to_array(raw_data, sample_width, n_channels)

                # 应用音量调整
                bg_volume_db = self.params.get('background_volume', -30.0)
                volume_factor = 10 ** (bg_volume_db / 20.0)
                audio_data = [s * volume_factor for s in audio_data]

                # 重采样背景音乐以匹配肯定语的采样率
                if framerate != target_sample_rate:
                    audio_data = self._resample_audio(audio_data, framerate, target_sample_rate)

                return {
                    'data': audio_data,
                    'sample_rate': target_sample_rate,
                    'channels': 1,
                    'sample_width': sample_width
                }

        except Exception as e:
            logger.error(f"加载背景音乐失败: {e}")
            return None

    def merge_audio(self, affirmation_data, background_data):
        """合并肯定语和背景音乐，最终长度与背景音乐一致"""
        logger.info("合并肯定语和背景音乐")

        aff_data = affirmation_data['data']

        # 如果没有背景音乐，只返回肯定语
        if background_data is None:
            return affirmation_data

        bg_data = background_data['data']
        bg_length = len(bg_data)
        aff_length = len(aff_data)

        # 检查是否启用确保完整性
        ensure_integrity = self.params.get('ensure_integrity', False)

        result = []

        if ensure_integrity:
            # 确保完整性模式：检测最后一次循环是否会被截断
            # 计算可以完整播放的循环次数
            full_cycles = bg_length // aff_length
            remaining_samples = bg_length % aff_length

            logger.info(f"确保完整性模式: 肯定语长度={aff_length}, 背景音乐长度={bg_length}, "
                       f"完整循环次数={full_cycles}, 剩余样本数={remaining_samples}")

            # 填充完整循环的肯定语
            for cycle in range(full_cycles):
                for j in range(aff_length):
                    idx = cycle * aff_length + j
                    mixed = aff_data[j] + bg_data[idx]
                    mixed = max(-1.0, min(1.0, mixed))
                    result.append(mixed)

            # 处理剩余部分：如果会被截断，则填充静音
            if remaining_samples > 0:
                logger.info(f"最后一次循环会被截断（剩余{remaining_samples}样本），填充静音")
                for i in range(remaining_samples):
                    idx = full_cycles * aff_length + i
                    # 只播放背景音乐（肯定语部分为静音）
                    mixed = bg_data[idx]
                    mixed = max(-1.0, min(1.0, mixed))
                    result.append(mixed)
        else:
            # 普通模式：肯定语循环播放填满整个背景音乐长度
            for i in range(bg_length):
                # 使用模运算实现循环播放
                aff_idx = i % aff_length
                mixed = aff_data[aff_idx] + bg_data[i]
                # 防止削波
                mixed = max(-1.0, min(1.0, mixed))
                result.append(mixed)

        return {
            'data': result,
            'sample_rate': affirmation_data['sample_rate'],
            'channels': 1,
            'sample_width': affirmation_data['sample_width']
        }

    def save_audio(self, audio_data):
        """保存音频到文件"""
        try:
            output_path = self.params['output_path']
            output_format = self.params.get('output_format', 'WAV')

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 转换为WAV原始数据
            raw_data = self._array_to_wav(audio_data['data'], audio_data['sample_width'])

            # 保存WAV文件
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(audio_data['channels'])
                wf.setsampwidth(audio_data['sample_width'])
                wf.setframerate(audio_data['sample_rate'])
                wf.writeframes(raw_data)

            logger.info(f"音频文件已保存: {output_path}")

            # 写入元数据（如果指定了标题或作者）
            self._write_metadata(output_path)

            return output_path

        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            return None

    def _write_metadata(self, audio_path):
        """使用FFmpeg写入元数据"""
        try:
            metadata_title = self.params.get('metadata_title', '').strip()
            metadata_author = self.params.get('metadata_author', '').strip()

            # 如果没有元数据需要写入，直接返回
            if not metadata_title and not metadata_author:
                return

            # 获取文件扩展名
            file_ext = os.path.splitext(audio_path)[1].lower()

            # 构建FFmpeg元数据参数
            metadata_args = []
            if metadata_title:
                metadata_args.extend(['-metadata', f'title={metadata_title}'])
            if metadata_author:
                metadata_args.extend(['-metadata', f'artist={metadata_author}'])

            # 创建临时文件路径
            temp_path = audio_path + '.temp' + file_ext

            # 构建FFmpeg命令
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',
                '-i', audio_path,
                '-c', 'copy',  # 直接复制，不重新编码
            ] + metadata_args + [
                temp_path
            ]

            logger.info(f"写入音频元数据: title={metadata_title}, artist={metadata_author}")

            # 执行FFmpeg命令
            import subprocess
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # 替换原文件
                os.replace(temp_path, audio_path)
                logger.info(f"音频元数据写入成功: {audio_path}")
            else:
                logger.warning(f"写入音频元数据失败: {result.stderr}")
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.warning(f"写入音频元数据时出错: {e}")

    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
        logger.info("音频处理已取消")
