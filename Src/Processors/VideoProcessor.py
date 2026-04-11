from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger
from .VideoCore import VideoCore


class VideoProcessor(QThread, VideoCore):
    """视频处理线程 - 使用FFmpeg生成视频（静态图片+音频）(GUI版本)"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)

    def __init__(self, params):
        QThread.__init__(self)
        VideoCore.__init__(self, params)

    def run(self):
        """执行视频生成"""
        try:
            logger.info("开始视频处理线程")

            def progress_callback(progress):
                self.progress_updated.emit(progress)

            success = self.generate_video(progress_callback=progress_callback)

            if success:
                output_path = self.params.get('video_output_path')
                self.processing_finished.emit(output_path)
            else:
                self.processing_error.emit(self.tr("视频生成失败"))

        except Exception as e:
            logger.error(f"视频处理出错: {e}")
            self.processing_error.emit(str(e))
