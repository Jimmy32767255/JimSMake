from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger
from .AudioCore import AudioCore


class AudioProcessor(QThread, AudioCore):
    """音频处理线程 - 处理肯定语和背景音乐的合并 (GUI版本)"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)

    def __init__(self, params):
        QThread.__init__(self)
        AudioCore.__init__(self, params)

    def run(self):
        """执行音频处理"""
        try:
            logger.info("开始音频处理线程")

            def progress_callback(progress):
                self.progress_updated.emit(progress)

            result = self.process(progress_callback=progress_callback)

            if result:
                self.processing_finished.emit(result)
            else:
                self.processing_error.emit(self.tr("保存音频文件失败"))

        except Exception as e:
            logger.error(f"音频处理出错: {e}")
            self.processing_error.emit(str(e))
