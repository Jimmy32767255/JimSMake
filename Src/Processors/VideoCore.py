"""
视频处理核心模块 - 不依赖 PyQt5
可以被 GUI 和 CLI 共同使用
"""

import os
import subprocess
from loguru import logger


class VideoCore:
    """视频处理核心类 - 纯逻辑，无 GUI 依赖"""

    def __init__(self, params=None):
        self.params = params or {}
        self.is_cancelled = False

    def set_params(self, params):
        """设置参数"""
        self.params = params

    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
        logger.info("视频处理已取消")

    def check_cancelled(self):
        """检查是否已取消"""
        return self.is_cancelled

    def generate_video(self, audio_path=None, image_path=None, output_path=None,
                       resolution=None, metadata_title=None, metadata_author=None,
                       progress_callback=None):
        """生成视频"""
        try:
            # 从参数中获取值
            if audio_path is None:
                audio_path = self.params.get('audio_path')
            if image_path is None:
                image_path = self.params.get('video_image')
            if output_path is None:
                output_path = self.params.get('video_output_path')
            if resolution is None:
                resolution = self.params.get('video_resolution', '1920x1080')
            if metadata_title is None:
                metadata_title = self.params.get('metadata_title', '').strip()
            if metadata_author is None:
                metadata_author = self.params.get('metadata_author', '').strip()

            logger.info("开始生成视频")

            if progress_callback:
                progress_callback(10)

            if self.check_cancelled():
                return False

            # 验证输入文件
            if not audio_path or not os.path.exists(audio_path):
                logger.error("音频文件不存在")
                return False

            if not image_path or not os.path.exists(image_path):
                logger.error("视觉化图片不存在")
                return False

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            if progress_callback:
                progress_callback(30)

            if self.check_cancelled():
                return False

            # 构建FFmpeg命令
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',
                '-loop', '1',
                '-i', image_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-s', resolution,
            ]

            # 添加元数据
            if metadata_title:
                ffmpeg_cmd.extend(['-metadata', f'title={metadata_title}'])
            if metadata_author:
                ffmpeg_cmd.extend(['-metadata', f'artist={metadata_author}'])

            ffmpeg_cmd.extend(['-shortest', output_path])

            logger.info(f"视频元数据: title={metadata_title}, artist={metadata_author}")
            logger.info(f"执行FFmpeg命令: {' '.join(ffmpeg_cmd)}")

            if progress_callback:
                progress_callback(50)

            if self.check_cancelled():
                return False

            # 执行FFmpeg命令
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if progress_callback:
                progress_callback(80)

            if self.check_cancelled():
                return False

            if result.returncode != 0:
                logger.error(f"FFmpeg执行失败: {result.stderr}")
                return False

            if progress_callback:
                progress_callback(100)

            logger.info(f"视频生成完成: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("视频生成超时")
            return False
        except Exception as e:
            logger.error(f"视频处理出错: {e}")
            return False
