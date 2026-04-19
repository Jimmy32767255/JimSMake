from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger
import os
from .VideoCore import VideoCore


class VideoProcessor(QThread, VideoCore):
    """视频处理线程 - 使用FFmpeg生成视频（静态图片+音频）(GUI版本)"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)

    def __init__(self, params):
        QThread.__init__(self)
        VideoCore.__init__(self, params)
        logger.debug(f"VideoProcessor初始化 - 参数: {params}")
        if params:
            audio_path = params.get('audio_path')
            video_image = params.get('video_image')
            video_output_path = params.get('video_output_path')
            logger.debug(f"VideoProcessor文件路径 - audio_path: {audio_path}, video_image: {video_image}, video_output_path: {video_output_path}")
            if audio_path:
                logger.debug(f"音频文件绝对路径: {os.path.abspath(audio_path)}, 是否存在: {os.path.exists(audio_path)}")
            if video_image:
                logger.debug(f"图片文件绝对路径: {os.path.abspath(video_image)}, 是否存在: {os.path.exists(video_image)}")
            if video_output_path:
                logger.debug(f"输出目录绝对路径: {os.path.abspath(os.path.dirname(video_output_path))}, 是否存在: {os.path.exists(os.path.dirname(video_output_path))}")

    def run(self):
        """执行视频生成"""
        try:
            logger.info("开始视频处理线程")
            logger.debug(f"VideoProcessor.run - 当前参数: {self.params}")

            def progress_callback(progress):
                self.progress_updated.emit(progress)

            success = self.generate_video(progress_callback=progress_callback)

            if success:
                output_path = self.params.get('video_output_path')
                logger.debug(f"视频生成成功，输出路径: {output_path}")
                self.processing_finished.emit(output_path)
            else:
                logger.error("视频生成失败")
                self.processing_error.emit(self.tr("视频生成失败"))

        except Exception as e:
            logger.error(f"视频处理出错: {e}")
            self.processing_error.emit(str(e))
