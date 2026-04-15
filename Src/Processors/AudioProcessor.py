from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger
import os
from .AudioCore import AudioCore


class AudioProcessor(QThread, AudioCore):
    """音频处理线程 - 处理肯定语和背景音乐的合并 (GUI版本)"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)

    def __init__(self, params):
        QThread.__init__(self)
        AudioCore.__init__(self, params)
        logger.debug(f"AudioProcessor初始化 - 参数: {params}")
        if params:
            affirmation_file = params.get('affirmation_file')
            background_file = params.get('background_file')
            output_path = params.get('output_path')
            logger.debug(f"AudioProcessor文件路径 - affirmation_file: {affirmation_file}, background_file: {background_file}, output_path: {output_path}")
            if affirmation_file:
                logger.debug(f"肯定语文件绝对路径: {os.path.abspath(affirmation_file)}, 是否存在: {os.path.exists(affirmation_file)}")
            if background_file:
                logger.debug(f"背景音文件绝对路径: {os.path.abspath(background_file)}, 是否存在: {os.path.exists(background_file)}")
            if output_path:
                output_dir = os.path.dirname(output_path)
                logger.debug(f"输出目录绝对路径: {os.path.abspath(output_dir) if output_dir else 'None'}, 是否存在: {os.path.exists(output_dir) if output_dir else False}")

    def run(self):
        """执行音频处理"""
        try:
            logger.info("开始音频处理线程")
            logger.debug(f"AudioProcessor.run - 当前参数: {self.params}")

            def progress_callback(progress):
                self.progress_updated.emit(progress)

            result = self.process(progress_callback=progress_callback)

            if result:
                logger.debug(f"音频处理成功，输出路径: {result}")
                self.processing_finished.emit(result)
            else:
                logger.error("音频处理失败")
                self.processing_error.emit(self.tr("保存音频文件失败"))

        except Exception as e:
            logger.error(f"音频处理出错: {e}")
            self.processing_error.emit(str(e))
