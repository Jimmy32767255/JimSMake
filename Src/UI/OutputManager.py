import os
from loguru import logger
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt


class OutputManager:
    """输出管理器 - 处理最终输出生成功能"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def generate_output(self):
        """生成最终输出"""
        logger.info("开始生成输出")

        if not self.main_window.check_project_selected():
            return

        try:
            project_dir = self.main_window.get_current_project_dir()
            if not project_dir:
                QMessageBox.warning(self.main_window, self.main_window.tr("错误"),
                                   self.main_window.tr("无法获取项目目录！"))
                return

            output_dir = os.path.join(project_dir, "Output")
            os.makedirs(output_dir, exist_ok=True)

            output_format = self.main_window.output_format.currentText()
            output_filename = f"output_{self._get_timestamp()}.{output_format.lower()}"
            output_path = os.path.join(output_dir, output_filename)

            progress = QProgressDialog(
                self.main_window.tr("正在生成输出..."),
                self.main_window.tr("取消"),
                0, 100,
                self.main_window
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            self._generate_audio(output_path, progress)

            progress.setValue(100)
            progress.close()

            logger.info(f"输出生成成功: {output_path}")
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"输出生成成功！\n保存位置: {output_path}"))

        except Exception as e:
            logger.error(f"生成输出失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"生成输出失败: {str(e)}"))

    def _generate_audio(self, output_path, progress):
        """生成音频文件"""
        logger.debug("开始生成音频")
        progress.setValue(20)

        affirmation_file = self.main_window.affirmation_file.text()
        bgm_file = self.main_window.bgm_file.text()

        if not affirmation_file or not os.path.exists(affirmation_file):
            raise Exception(self.main_window.tr("请选择肯定语音频文件！"))

        if self.main_window.bgm_enabled.isChecked() and (not bgm_file or not os.path.exists(bgm_file)):
            raise Exception(self.main_window.tr("背景音乐文件不存在！"))

        audio_processor = self.main_window.AudioProcessor()
        
        if self.main_window.bgm_enabled.isChecked():
            progress.setValue(50)
            audio_processor.mix_audio(
                affirmation_file,
                bgm_file,
                output_path,
                self.main_window.bgm_volume.value() / 100.0
            )
        else:
            progress.setValue(50)
            audio_processor.copy_audio(affirmation_file, output_path)

        progress.setValue(80)

        if self.main_window.freq_track_enabled.isChecked():
            freq_file = self._generate_freq_track()
            audio_processor.mix_audio(output_path, freq_file, output_path, 0.3)

        progress.setValue(90)
        logger.debug("音频生成完成")

    def _generate_freq_track(self):
        """生成特定频率音轨"""
        freq = self.main_window.freq_spin.value()
        duration = self.main_window.freq_duration.value()
        output_path = os.path.join(
            self.main_window.get_current_project_dir(),
            "Output",
            f"freq_{freq}hz.wav"
        )
        
        audio_processor = self.main_window.AudioProcessor()
        audio_processor.generate_sine_wave(freq, duration, output_path)
        return output_path

    def _get_timestamp(self):
        """获取时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")