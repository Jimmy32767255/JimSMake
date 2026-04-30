import os
import pyttsx3
from loguru import logger
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt

class TTSManager:
    """TTS管理器 - 处理文本转语音功能"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def generate_tts_audio(self):
        """使用TTS引擎生成肯定语音频"""
        logger.info("开始生成TTS音频")

        if not self._check_project_selected():
            return

        try:
            if not self.main_window.affirmation_text.text().strip():
                logger.warning("未输入肯定语文本")
                QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                                   self.main_window.tr("请输入肯定语文本！"))
                return

            output_dir = self._get_affirmation_output_dir()
            if not output_dir:
                QMessageBox.warning(self.main_window, self.main_window.tr("错误"),
                                   self.main_window.tr("无法获取项目目录！"))
                return

            os.makedirs(output_dir, exist_ok=True)

            selected_engine = self.main_window.tts_engine.currentText()
            output_filename = f"{selected_engine.lower().replace(' ', '-')}.wav"
            output_path = os.path.join(output_dir, output_filename)

            engine = pyttsx3.init()
            
            voices = engine.getProperty('voices')
            for voice in voices:
                if selected_engine in voice.name:
                    engine.setProperty('voice', voice.id)
                    break

            engine.setProperty('rate', self.main_window.tts_rate.value())
            engine.setProperty('volume', self.main_window.tts_volume.value() / 100.0)

            progress = QProgressDialog(
                self.main_window.tr("正在生成TTS音频..."),
                self.main_window.tr("取消"),
                0, 100,
                self.main_window
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            def on_word(name, location, length):
                progress.setValue(min(95, progress.value() + 1))

            engine.connect('started-word', on_word)
            engine.save_to_file(self.main_window.affirmation_text.text(), output_path)
            engine.runAndWait()
            
            progress.setValue(100)
            progress.close()

            self.main_window.affirmation_file.setText(output_path)
            
            logger.info(f"TTS音频生成成功: {output_path}")
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"TTS音频生成成功！\n保存位置: {output_path}"))

        except Exception as e:
            logger.error(f"TTS音频生成失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"TTS音频生成失败: {str(e)}"))

    def _get_affirmation_output_dir(self):
        """获取肯定语输出目录"""
        project_dir = self.main_window.get_current_project_dir()
        if project_dir:
            return os.path.join(project_dir, "Assets", "Affirmation")
        return None

    def _check_project_selected(self):
        """检查是否选择了项目"""
        if not hasattr(self.main_window, 'current_project_name') or not self.main_window.current_project_name:
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目！"))
            return False
        return True