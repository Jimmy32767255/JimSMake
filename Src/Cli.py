"""
SMake CLI 模块 - 命令行界面支持
在 GUI 启动失败或传入 -C/--cli 参数时启动
"""

import os
import sys
import argparse
import wave
import struct
import math
import subprocess
import tempfile
from pathlib import Path
from loguru import logger


class CLIProcessor:
    """CLI 音频/视频处理器 - 不依赖 PyQt5"""

    def __init__(self):
        self.is_cancelled = False
        self.progress_callback = None

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def _update_progress(self, progress):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(progress)
        else:
            logger.info(f"进度: {progress}%")

    def _wav_to_array(self, raw_data, sample_width, channels):
        """将WAV原始数据转换为列表"""
        audio_data = []

        if sample_width == 1:
            for i in range(0, len(raw_data), channels):
                if channels == 1:
                    val = raw_data[i] - 128
                    audio_data.append(val / 128.0)
                else:
                    avg = sum(raw_data[i + j] - 128 for j in range(channels)) / channels
                    audio_data.append(avg / 128.0)

        elif sample_width == 2:
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

        elif sample_width == 3:
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

        elif sample_width == 4:
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

        if sample_width == 1:
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 127 + 128)
                raw_data.append(val & 0xFF)

        elif sample_width == 2:
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 32767)
                raw_data.extend(struct.pack('<h', val))

        elif sample_width == 3:
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 8388607)
                raw_data.extend(val.to_bytes(3, byteorder='little', signed=True))

        elif sample_width == 4:
            for sample in audio_data:
                val = int(max(-1.0, min(1.0, sample)) * 2147483647)
                raw_data.extend(struct.pack('<i', val))

        return bytes(raw_data)

    def _resample_audio(self, data, src_rate, dst_rate):
        """重采样音频数据"""
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
        """改变音频速度"""
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

    def load_affirmation_audio(self, file_path):
        """加载肯定语音频文件"""
        try:
            logger.info(f"加载肯定语音频: {file_path}")

            if not os.path.exists(file_path):
                logger.error(f"肯定语音频文件不存在: {file_path}")
                return None

            with wave.open(file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_data = wf.readframes(n_frames)
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

    def process_affirmation_effects(self, audio_data, params):
        """处理肯定语效果"""
        data = audio_data['data']
        sample_rate = audio_data['sample_rate']

        speed = params.get('speed', 1.0)
        if speed != 1.0:
            logger.info(f"应用倍速: {speed}x")
            data = self._change_speed(data, speed)
            sample_rate = int(sample_rate * speed)

        if params.get('reverse', False):
            logger.info("应用倒放效果")
            data = data[::-1]

        freq_mode = params.get('frequency_mode', 0)
        if freq_mode == 1:
            logger.info("应用UG频率模式（亚超声波）")
            data = self._apply_ug_frequency(data, sample_rate)
        elif freq_mode == 2:
            logger.info("应用传统频率模式（次声波）")
            data = self._apply_traditional_frequency(data, sample_rate)

        volume_db = params.get('volume', 0.0)
        if volume_db != 0.0:
            volume_factor = 10 ** (volume_db / 20.0)
            logger.info(f"应用音量调整: {volume_db}dB")
            data = [s * volume_factor for s in data]

        audio_data['data'] = data
        audio_data['sample_rate'] = sample_rate
        return audio_data

    def apply_overlay(self, audio_data, params):
        """应用叠加效果"""
        overlay_times = params.get('overlay_times', 1)
        overlay_interval = params.get('overlay_interval', 1.0)
        volume_decrease = params.get('volume_decrease', 0.0)

        if overlay_times <= 1:
            return audio_data

        logger.info(f"应用叠加效果: {overlay_times}次")

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

    def load_background_audio(self, file_path, target_sample_rate, bg_volume_db):
        """加载并处理背景音乐"""
        if not file_path or not os.path.exists(file_path):
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

                volume_factor = 10 ** (bg_volume_db / 20.0)
                audio_data = [s * volume_factor for s in audio_data]

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

    def merge_audio(self, affirmation_data, background_data, ensure_integrity):
        """合并肯定语和背景音乐"""
        logger.info("合并音频")

        aff_data = affirmation_data['data']

        if background_data is None:
            return affirmation_data

        bg_data = background_data['data']
        bg_length = len(bg_data)
        aff_length = len(aff_data)
        result = []

        if ensure_integrity:
            full_cycles = bg_length // aff_length
            remaining_samples = bg_length % aff_length

            logger.info(f"确保完整性模式: 完整循环次数={full_cycles}")

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

        return {
            'data': result,
            'sample_rate': affirmation_data['sample_rate'],
            'channels': 1,
            'sample_width': affirmation_data['sample_width']
        }

    def save_audio_wav(self, audio_data, output_path):
        """保存为WAV格式"""
        raw_data = self._array_to_wav(audio_data['data'], audio_data['sample_width'])

        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(audio_data['channels'])
            wf.setsampwidth(audio_data['sample_width'])
            wf.setframerate(audio_data['sample_rate'])
            wf.writeframes(raw_data)

        logger.info(f"WAV音频文件已保存: {output_path}")
        return output_path

    def save_audio_mp3(self, audio_data, output_path, metadata_title='', metadata_author=''):
        """使用FFmpeg保存为MP3格式"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            raw_data = self._array_to_wav(audio_data['data'], audio_data['sample_width'])
            with wave.open(temp_wav_path, 'wb') as wf:
                wf.setnchannels(audio_data['channels'])
                wf.setsampwidth(audio_data['sample_width'])
                wf.setframerate(audio_data['sample_rate'])
                wf.writeframes(raw_data)

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

            result = subprocess.run(
                ffmpeg_cmd, capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                logger.info(f"MP3音频文件已保存: {output_path}")
                return output_path
            else:
                logger.error(f"FFmpeg转换MP3失败: {result.stderr}")
                return None

        finally:
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

    def generate_video(self, audio_path, image_path, output_path, resolution='1920x1080',
                       metadata_title='', metadata_author=''):
        """生成视频"""
        try:
            logger.info("开始生成视频")

            if not os.path.exists(audio_path):
                logger.error("音频文件不存在")
                return False

            if not os.path.exists(image_path):
                logger.error("视觉化图片不存在")
                return False

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            ffmpeg_cmd = [
                'ffmpeg', '-y', '-loop', '1', '-i', image_path,
                '-i', audio_path, '-c:v', 'libx264', '-tune', 'stillimage',
                '-c:a', 'aac', '-b:a', '192k', '-pix_fmt', 'yuv420p',
                '-s', resolution
            ]

            if metadata_title:
                ffmpeg_cmd.extend(['-metadata', f'title={metadata_title}'])
            if metadata_author:
                ffmpeg_cmd.extend(['-metadata', f'artist={metadata_author}'])

            ffmpeg_cmd.extend(['-shortest', output_path])

            logger.info(f"执行FFmpeg命令")

            result = subprocess.run(
                ffmpeg_cmd, capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                logger.info(f"视频文件已保存: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg生成视频失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"生成视频时出错: {e}")
            return False

    def process(self, params):
        """执行完整的处理流程"""
        try:
            logger.info("开始CLI音频处理")
            self._update_progress(5)

            if self.is_cancelled:
                return None

            affirmation_data = self.load_affirmation_audio(params['affirmation_file'])
            if affirmation_data is None:
                logger.error("加载肯定语音频失败")
                return None
            self._update_progress(20)

            if self.is_cancelled:
                return None

            affirmation_data = self.process_affirmation_effects(affirmation_data, params)
            self._update_progress(40)

            if self.is_cancelled:
                return None

            affirmation_data = self.apply_overlay(affirmation_data, params)
            self._update_progress(60)

            if self.is_cancelled:
                return None

            background_data = self.load_background_audio(
                params.get('background_file', ''),
                affirmation_data['sample_rate'],
                params.get('background_volume', -23.0)
            )
            self._update_progress(75)

            if self.is_cancelled:
                return None

            final_data = self.merge_audio(
                affirmation_data, background_data,
                params.get('ensure_integrity', False)
            )
            self._update_progress(90)

            if self.is_cancelled:
                return None

            output_path = params['output_path']
            output_format = params.get('output_format', 'WAV').upper()

            if output_format == 'MP3':
                result = self.save_audio_mp3(
                    final_data, output_path,
                    params.get('metadata_title', ''),
                    params.get('metadata_author', '')
                )
            else:
                result = self.save_audio_wav(final_data, output_path)
                if result:
                    self._write_metadata(output_path, params)

            self._update_progress(100)

            if result:
                logger.info(f"处理完成: {output_path}")
                return output_path
            else:
                logger.error("保存音频文件失败")
                return None

        except Exception as e:
            logger.error(f"处理出错: {e}")
            return None

    def _write_metadata(self, audio_path, params):
        """使用FFmpeg写入元数据"""
        try:
            metadata_title = params.get('metadata_title', '').strip()
            metadata_author = params.get('metadata_author', '').strip()

            if not metadata_title and not metadata_author:
                return

            metadata_args = []
            if metadata_title:
                metadata_args.extend(['-metadata', f'title={metadata_title}'])
            if metadata_author:
                metadata_args.extend(['-metadata', f'artist={metadata_author}'])

            temp_path = audio_path + '.temp.wav'

            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', audio_path, '-c', 'copy'
            ] + metadata_args + [temp_path]

            logger.info(f"写入音频元数据")

            result = subprocess.run(
                ffmpeg_cmd, capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                os.replace(temp_path, audio_path)
                logger.info("音频元数据写入成功")
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.warning(f"写入音频元数据时出错: {e}")

    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
        logger.info("处理已取消")


class SMakeCLI:
    """SMake 命令行界面"""

    def __init__(self):
        self.processor = CLIProcessor()

    def run(self, args=None):
        """运行CLI"""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.version:
            logger.info("SMake CLI v1.0")
            return 0

        if not parsed_args.affirmation:
            logger.error("错误: 必须指定肯定语音频文件 (-a/--affirmation)")
            parser.print_help()
            return 1

        if not parsed_args.output:
            logger.error("错误: 必须指定输出文件路径 (-o/--output)")
            parser.print_help()
            return 1

        params = {
            'affirmation_file': parsed_args.affirmation,
            'output_path': parsed_args.output,
            'output_format': parsed_args.format.upper(),
            'background_file': parsed_args.background,
            'volume': parsed_args.volume,
            'background_volume': parsed_args.bg_volume,
            'frequency_mode': parsed_args.freq_mode,
            'speed': parsed_args.speed,
            'reverse': parsed_args.reverse,
            'overlay_times': parsed_args.overlay_times,
            'overlay_interval': parsed_args.overlay_interval,
            'volume_decrease': parsed_args.volume_decrease,
            'ensure_integrity': parsed_args.ensure_integrity,
            'metadata_title': parsed_args.title or '',
            'metadata_author': parsed_args.author or ''
        }

        logger.info(f"开始处理...")
        logger.info(f"肯定语: {params['affirmation_file']}")
        logger.info(f"输出: {params['output_path']}")
        if params['background_file']:
            logger.info(f"背景音: {params['background_file']}")

        result = self.processor.process(params)

        if result:
            logger.success(f"成功! 输出文件: {result}")

            if parsed_args.video and parsed_args.image:
                video_path = os.path.splitext(result)[0] + '.mp4'
                success = self.processor.generate_video(
                    result, parsed_args.image, video_path,
                    parsed_args.resolution,
                    params['metadata_title'],
                    params['metadata_author']
                )
                if success:
                    logger.success(f"视频生成成功: {video_path}")
                else:
                    logger.error("视频生成失败")

            return 0
        else:
            logger.error("\n处理失败!")
            return 1

    def _create_parser(self):
        """创建参数解析器"""
        parser = argparse.ArgumentParser(
            prog='smake',
            description='SMake - 潜意识音频生成器 (CLI模式)',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  python -m Src.Cli -a affirmation.wav -o output.wav
  python -m Src.Cli -a aff.wav -b bg.wav -o out.mp3 -f MP3
  python -m Src.Cli -a aff.wav -o out.wav --freq-mode 1 --speed 1.5
  python -m Src.Cli -a aff.wav -o out.wav -v image.jpg --video
            """
        )

        parser.add_argument('-a', '--affirmation', required=True,
                            help='肯定语音频文件路径 (WAV格式)')
        parser.add_argument('-o', '--output', required=True,
                            help='输出文件路径')
        parser.add_argument('-b', '--background',
                            help='背景音文件路径 (WAV格式)')
        parser.add_argument('-f', '--format', default='WAV',
                            choices=['WAV', 'MP3'],
                            help='输出格式 (默认: WAV)')

        parser.add_argument('--volume', type=float, default=-23.0,
                            help='肯定语音量调整 (dB, 默认: -23)')
        parser.add_argument('--bg-volume', type=float, default=0.0,
                            help='背景音量调整 (dB, 默认: 0)')

        parser.add_argument('--freq-mode', type=int, default=0,
                            choices=[0, 1, 2],
                            help='频率模式: 0=Raw, 1=UG(亚超声波), 2=传统(次声波) (默认: 0)')
        parser.add_argument('--speed', type=float, default=1.0,
                            help='倍速 (默认: 1.0)')
        parser.add_argument('--reverse', action='store_true',
                            help='倒放肯定语')

        parser.add_argument('--overlay-times', type=int, default=1,
                            help='叠加次数 (默认: 1)')
        parser.add_argument('--overlay-interval', type=float, default=1.0,
                            help='叠加间隔 (秒, 默认: 1.0)')
        parser.add_argument('--volume-decrease', type=float, default=0.0,
                            help='每次叠加音量递减 (dB, 默认: 0)')

        parser.add_argument('--ensure-integrity', action='store_true',
                            help='确保肯定语完整性')

        parser.add_argument('-v', '--image',
                            help='视觉化图片路径 (用于视频生成)')
        parser.add_argument('--video', action='store_true',
                            help='同时生成视频')
        parser.add_argument('--resolution', default='1920x1080',
                            help='视频分辨率 (默认: 1920x1080)')

        parser.add_argument('--title',
                            help='音频/视频标题元数据')
        parser.add_argument('--author',
                            help='音频/视频作者元数据')

        parser.add_argument('--version', action='store_true',
                            help='显示版本信息')

        return parser


def main():
    """CLI入口函数"""
    logger.remove()
    logger.add(sys.stderr, level="INFO",
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    cli = SMakeCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())
