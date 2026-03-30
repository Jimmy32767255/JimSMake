from PyQt5.QtCore import QThread, pyqtSignal
import os
import subprocess
from loguru import logger


class VideoProcessor(QThread):
    """视频处理线程 - 使用FFmpeg生成视频（静态图片+音频）"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_cancelled = False

    def run(self):
        """执行视频生成"""
        try:
            logger.info("开始视频处理线程")
            self.progress_updated.emit(10)

            if self.is_cancelled:
                return

            # 获取参数
            audio_path = self.params.get('audio_path')
            image_path = self.params.get('video_image')
            output_path = self.params.get('video_output_path')
            video_format = self.params.get('video_format', 'MP4')
            resolution = self.params.get('video_resolution', '1920x1080')

            # 验证输入文件
            if not audio_path or not os.path.exists(audio_path):
                self.processing_error.emit(self.tr("音频文件不存在"))
                return

            if not image_path or not os.path.exists(image_path):
                self.processing_error.emit(self.tr("视觉化图片不存在"))
                return

            self.progress_updated.emit(30)

            if self.is_cancelled:
                return

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 获取元数据
            metadata_title = self.params.get('metadata_title', '').strip()
            metadata_author = self.params.get('metadata_author', '').strip()

            # 构建FFmpeg命令
            # 使用静态图片和音频生成视频
            # -loop 1: 循环输入图片
            # -i {image_path}: 输入图片
            # -i {audio_path}: 输入音频
            # -c:v libx264: 视频编码器
            # -tune stillimage: 针对静态图片优化
            # -c:a aac: 音频编码器
            # -b:a 192k: 音频比特率
            # -pix_fmt yuv420p: 像素格式（兼容性）
            # -shortest: 以最短输入为准（音频长度）
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # 覆盖输出文件
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

            # 添加元数据（如果指定了）
            if metadata_title:
                ffmpeg_cmd.extend(['-metadata', f'title={metadata_title}'])
            if metadata_author:
                ffmpeg_cmd.extend(['-metadata', f'artist={metadata_author}'])

            ffmpeg_cmd.extend(['-shortest', output_path])

            logger.info(f"视频元数据: title={metadata_title}, artist={metadata_author}")

            logger.info(f"执行FFmpeg命令: {' '.join(ffmpeg_cmd)}")

            self.progress_updated.emit(50)

            if self.is_cancelled:
                return

            # 执行FFmpeg命令
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            self.progress_updated.emit(80)

            if self.is_cancelled:
                return

            if result.returncode != 0:
                logger.error(f"FFmpeg执行失败: {result.stderr}")
                self.processing_error.emit(f"FFmpeg错误: {result.stderr}")
                return

            self.progress_updated.emit(100)

            logger.info(f"视频生成完成: {output_path}")
            self.processing_finished.emit(output_path)

        except subprocess.TimeoutExpired:
            logger.error("视频生成超时")
            self.processing_error.emit(self.tr("视频生成超时"))
        except Exception as e:
            logger.error(f"视频处理出错: {e}")
            self.processing_error.emit(str(e))

    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
        logger.info("视频处理已取消")
