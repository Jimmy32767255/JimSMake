from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger
import os
from .DecompileCore import DecompileCore

class DecompileProcessor(QThread, DecompileCore):
    """音频反编译处理线程 - 处理音频反编译 (GUI版本)"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)
    preview_ready = pyqtSignal(object)  # 预览音频数据准备好

    def __init__(self, params):
        QThread.__init__(self)
        DecompileCore.__init__(self, params)
        self.mode = 'export'  # 'export' 或 'preview'
        self.audio_info = None  # 用于预览的音频数据
        logger.debug(f"DecompileProcessor初始化 - 参数: {params}")

    def set_mode(self, mode):
        """设置处理模式"""
        self.mode = mode  # 'export' 或 'preview'

    def set_audio_info(self, audio_info):
        """设置音频数据（用于预览）"""
        self.audio_info = audio_info

    def run(self):
        """执行反编译处理"""
        try:
            if self.mode == 'preview':
                self._run_preview()
            else:
                self._run_export()
        except Exception as e:
            logger.error(f"反编译处理出错: {e}")
            self.processing_error.emit(str(e))

    def _run_preview(self):
        """运行预览生成"""
        logger.info("开始生成反编译预览")

        def progress_callback(progress):
            self.progress_updated.emit(progress)

        result = self.generate_preview(self.audio_info, self.params, progress_callback)

        if result:
            logger.debug("预览生成成功")
            self.preview_ready.emit(result)
        else:
            logger.error("预览生成失败")
            self.processing_error.emit(self.tr("生成预览失败"))

    def _run_export(self):
        """运行导出处理"""
        logger.info("开始反编译导出")

        def progress_callback(progress):
            self.progress_updated.emit(progress)

        result = self.process(progress_callback=progress_callback)

        if result:
            logger.debug(f"反编译成功，输出路径: {result}")
            self.processing_finished.emit(result)
        else:
            logger.error("反编译失败")
            self.processing_error.emit(self.tr("导出音频文件失败"))


class DecompilePlayer(QThread):
    """反编译音频播放器线程"""
    position_changed = pyqtSignal(int)  # 播放位置变化（毫秒）
    duration_changed = pyqtSignal(int)  # 总时长变化（毫秒）
    playback_finished = pyqtSignal()
    playback_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.audio_data = None
        self.sample_rate = 44100
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.volume = 1.0

    def set_audio(self, audio_info):
        """设置要播放的音频数据"""
        if audio_info:
            self.audio_data = audio_info['data']
            self.sample_rate = audio_info['sample_rate']
            duration_ms = int(len(self.audio_data) / self.sample_rate * 1000)
            self.duration_changed.emit(duration_ms)
            self.current_position = 0

    def play(self):
        """开始播放"""
        if not self.is_playing:
            self.is_playing = True
            self.is_paused = False
            self.start()
        elif self.is_paused:
            self.is_paused = False

    def pause(self):
        """暂停播放"""
        self.is_paused = True

    def stop(self):
        """停止播放"""
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.position_changed.emit(0)

    def seek(self, position_ms):
        """跳转到指定位置（毫秒）"""
        if self.audio_data:
            self.current_position = int(position_ms / 1000 * self.sample_rate)
            self.current_position = max(0, min(self.current_position, len(self.audio_data)))

    def set_volume(self, volume):
        """设置音量 (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))

    def run(self):
        """播放线程"""
        try:
            import sounddevice as sd

            if not self.audio_data:
                self.playback_error.emit("没有音频数据")
                return

            chunk_size = 1024
            total_samples = len(self.audio_data)

            while self.is_playing and self.current_position < total_samples:
                if self.is_paused:
                    self.msleep(100)
                    continue

                end_pos = min(self.current_position + chunk_size, total_samples)
                chunk = self.audio_data[self.current_position:end_pos]

                # 应用音量
                chunk = [s * self.volume for s in chunk]

                # 播放音频块
                sd.play(chunk, self.sample_rate, blocking=False)
                sd.wait()

                self.current_position = end_pos

                # 发送位置更新
                position_ms = int(self.current_position / self.sample_rate * 1000)
                self.position_changed.emit(position_ms)

            if self.current_position >= total_samples:
                self.playback_finished.emit()

        except ImportError:
            self.playback_error.emit("未安装 sounddevice 库，无法播放音频")
        except Exception as e:
            self.playback_error.emit(f"播放错误: {str(e)}")
        finally:
            self.is_playing = False
