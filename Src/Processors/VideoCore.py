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
        logger.debug(f"VideoCore初始化 - 参数: {params}")
        if params:
            audio_path = params.get('audio_path')
            video_image = params.get('video_image')
            video_output_path = params.get('video_output_path')
            logger.debug(f"VideoCore初始化文件路径 - audio_path: {audio_path}, video_image: {video_image}, video_output_path: {video_output_path}")
            if audio_path:
                logger.debug(f"音频文件绝对路径: {os.path.abspath(audio_path)}, 是否存在: {os.path.exists(audio_path)}")
            if video_image:
                logger.debug(f"图片文件绝对路径: {os.path.abspath(video_image)}, 是否存在: {os.path.exists(video_image)}")
            if video_output_path:
                output_dir = os.path.dirname(video_output_path)
                logger.debug(f"输出目录绝对路径: {os.path.abspath(output_dir) if output_dir else 'None'}, 是否存在: {os.path.exists(output_dir) if output_dir else False}")

    def set_params(self, params):
        """设置参数"""
        logger.debug(f"VideoCore.set_params - 设置参数: {params}")
        self.params = params
        audio_path = params.get('audio_path')
        video_image = params.get('video_image')
        video_output_path = params.get('video_output_path')
        logger.debug(f"VideoCore.set_params文件路径 - audio_path: {audio_path}, video_image: {video_image}, video_output_path: {video_output_path}")

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
            logger.debug(f"generate_video参数 - audio_path: {audio_path}, image_path: {image_path}, output_path: {output_path}")
            logger.debug(f"generate_video文件路径详情:")
            if audio_path:
                logger.debug(f"  音频文件绝对路径: {os.path.abspath(audio_path)}, 是否存在: {os.path.exists(audio_path)}")
            if image_path:
                logger.debug(f"  图片文件绝对路径: {os.path.abspath(image_path)}, 是否存在: {os.path.exists(image_path)}")
            if output_path:
                output_dir = os.path.dirname(output_path)
                logger.debug(f"  输出目录绝对路径: {os.path.abspath(output_dir) if output_dir else 'None'}, 是否存在: {os.path.exists(output_dir) if output_dir else False}")

            if progress_callback:
                progress_callback(10)

            if self.check_cancelled():
                return False

            # 验证输入文件
            if not audio_path or not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                if audio_path:
                    logger.debug(f"音频文件绝对路径: {os.path.abspath(audio_path)}")
                return False

            if not image_path or not os.path.exists(image_path):
                logger.error(f"视觉化图片不存在: {image_path}")
                if image_path:
                    logger.debug(f"图片文件绝对路径: {os.path.abspath(image_path)}")
                return False

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            logger.debug(f"检查输出目录: {output_dir}")
            if output_dir and not os.path.exists(output_dir):
                logger.debug(f"输出目录不存在，创建目录: {os.path.abspath(output_dir)}")
                os.makedirs(output_dir, exist_ok=True)
                logger.debug(f"输出目录创建成功: {os.path.abspath(output_dir)}")

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
            logger.debug(f"FFmpeg完整命令参数: {ffmpeg_cmd}")
            logger.debug(f"输出文件路径: {output_path}, 绝对路径: {os.path.abspath(output_path)}")

            if progress_callback:
                progress_callback(50)

            if self.check_cancelled():
                return False

            # 执行FFmpeg命令
            logger.debug("开始执行FFmpeg子进程")
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            logger.debug(f"FFmpeg返回码: {result.returncode}")

            if progress_callback:
                progress_callback(80)

            if self.check_cancelled():
                return False

            if result.returncode != 0:
                logger.error(f"FFmpeg执行失败: {result.stderr}")
                return False

            if progress_callback:
                progress_callback(100)

            # 验证输出文件
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.debug(f"输出文件创建成功: {output_path}, 大小: {file_size} bytes, 绝对路径: {os.path.abspath(output_path)}")
            else:
                logger.warning(f"输出文件可能未创建: {output_path}")

            logger.info(f"视频生成完成: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("视频生成超时")
            return False
        except Exception as e:
            logger.error(f"视频处理出错: {e}")
            return False
