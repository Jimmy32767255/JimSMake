import os
from loguru import logger
from PyQt5.QtWidgets import QMessageBox


class RecordingManager:
    """录音管理器 - 处理录音控制功能"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.recorder = None
        
    def toggle_recording(self):
        """切换录音状态"""
        if self.main_window.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """开始录音"""
        logger.info("开始录音")

        if not self.main_window.check_project_selected():
            return

        output_dir = self._get_affirmation_output_dir()
        if not output_dir:
            return

        os.makedirs(output_dir, exist_ok=True)

        timestamp = self._get_timestamp()
        output_file = os.path.join(output_dir, f"recording_{timestamp}.wav")

        device_index = self.main_window.record_device.currentData()
        if device_index is None or device_index == "":
            device_index = None

        self.recorder = self.main_window.AudioRecorder(
            device_index=device_index,
            sample_rate=44100,
            channels=1
        )
        self.recorder.set_output_file(output_file)
        self.recorder.recording_finished.connect(self.on_recording_finished)
        self.recorder.recording_error.connect(self.on_recording_error)
        self.recorder.start()

        self.main_window.is_recording = True
        self.main_window.record_btn.setText(self.main_window.tr("停止录制"))
        self.main_window.record_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")
        self.main_window.record_btn.setChecked(True)

        logger.info(f"录音已开始，输出文件: {output_file}")

    def stop_recording(self):
        """停止录音"""
        logger.info("停止录音")

        if self.recorder:
            self.recorder.stop()
            self.recorder.wait()

        self.main_window.is_recording = False
        self.main_window.record_btn.setText(self.main_window.tr("开始录制"))
        self.main_window.record_btn.setStyleSheet("")
        self.main_window.record_btn.setChecked(False)

        logger.info("录音已停止")

    def on_recording_finished(self, file_path):
        """录音完成回调"""
        logger.info(f"录音完成: {file_path}")
        self.main_window.affirmation_file.setText(file_path)
        QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                               self.main_window.tr(f"录音完成！文件已保存到:\n{file_path}"))

    def on_recording_error(self, error_message):
        """录音错误回调"""
        logger.error(f"录音错误: {error_message}")
        self.main_window.is_recording = False
        self.main_window.record_btn.setText(self.main_window.tr("开始录制"))
        self.main_window.record_btn.setStyleSheet("")
        self.main_window.record_btn.setChecked(False)
        QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                           self.main_window.tr(f"录音失败: {error_message}"))

    def _get_affirmation_output_dir(self):
        """获取肯定语输出目录"""
        project_dir = self.main_window.get_current_project_dir()
        if project_dir:
            return os.path.join(project_dir, "Assets", "Affirmation")
        return None

    def _get_timestamp(self):
        """获取时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")