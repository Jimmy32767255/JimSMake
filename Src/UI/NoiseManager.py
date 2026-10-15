import os
from loguru import logger
from PyQt5.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt
from Processors.AudioCore import AudioCore


class NoiseManager:
    """白噪音管理器 - 处理白噪音背景音生成功能"""

    # 未设置肯定语时的默认白噪音时长（秒）
    DEFAULT_DURATION = 60.0
    # 默认输出文件名（与 DirInfo 中的背景音乐约定一致）
    DEFAULT_FILENAME = "BGM.wav"

    def __init__(self, main_window):
        self.main_window = main_window
        self.audio_core = AudioCore()

    def get_default_output_path(self, project_dir=None):
        """获取默认白噪音输出路径"""
        if project_dir is None:
            project_dir = self.main_window.get_current_project_dir()
        if project_dir:
            return os.path.join(project_dir, "Assets", self.DEFAULT_FILENAME)
        return ""

    def generate_white_noise(self):
        """按当前设置生成白噪音背景音文件"""
        logger.info("开始生成白噪音")

        if not self._check_project_selected():
            return

        project_dir = self.main_window.get_current_project_dir()
        if not project_dir:
            QMessageBox.warning(self.main_window, self.main_window.tr("错误"),
                                self.main_window.tr("无法获取项目目录！"))
            return

        try:
            output_path = self._resolve_output_path(project_dir)
            seed = self._parse_seed(self.main_window.white_noise_seed.text())
            duration = self._get_duration(project_dir)

            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self.main_window, self.main_window.tr("确认覆盖"),
                    self.main_window.tr(f"文件已存在，是否覆盖？\n{output_path}"),
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    logger.info(f"用户取消覆盖: {output_path}")
                    return

            progress = QProgressDialog(
                self.main_window.tr("正在生成白噪音..."),
                None,
                0, 100,
                self.main_window
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()

            def on_progress(percent):
                progress.setValue(percent)
                QApplication.processEvents()

            output_path, used_seed = self.audio_core.generate_white_noise(
                output_path, duration, seed=seed, progress_callback=on_progress)

            progress.setValue(100)
            progress.close()

            self.main_window.white_noise_output.setText(output_path)
            self.main_window.white_noise_seed.setText(str(used_seed))

            # 背景音文件为空时自动填入生成结果，方便直接使用
            if not self.main_window.background_file.text().strip():
                self.main_window.background_file.setText(output_path)

            self.main_window.project_manager.update_noise_settings(
                project_dir, self.main_window.white_noise_output.text(), used_seed)

            logger.info(f"白噪音生成成功: {output_path}, 种子: {used_seed}")
            QMessageBox.information(
                self.main_window, self.main_window.tr("成功"),
                self.main_window.tr(f"白噪音生成成功！\n保存位置: {output_path}\n随机种子: {used_seed}"))

        except Exception as e:
            logger.error(f"白噪音生成失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                                 self.main_window.tr(f"白噪音生成失败: {str(e)}"))

    def _get_duration(self, project_dir):
        """获取白噪音时长 - 与肯定语音频时长一致，未设置时使用默认值"""
        affirmation_path = self.main_window.affirmation_file.text().strip()
        if affirmation_path:
            if not os.path.isabs(affirmation_path):
                affirmation_path = os.path.join(project_dir, affirmation_path)
            if os.path.exists(affirmation_path):
                duration = self.main_window.get_audio_duration(affirmation_path)
                if duration and duration > 0:
                    logger.info(f"白噪音时长跟随肯定语: {duration}s")
                    return duration
            else:
                logger.warning(f"肯定语音频不存在，使用默认时长: {affirmation_path}")

        logger.info(f"使用默认白噪音时长: {self.DEFAULT_DURATION}s")
        return self.DEFAULT_DURATION

    def _resolve_output_path(self, project_dir):
        """解析白噪音输出路径"""
        path = self.main_window.white_noise_output.text().strip()
        if not path:
            path = os.path.join(project_dir, "Assets", self.DEFAULT_FILENAME)
        elif not os.path.isabs(path):
            path = os.path.join(project_dir, path)

        if not path.lower().endswith('.wav'):
            path += '.wav'

        return os.path.normpath(path)

    @staticmethod
    def _parse_seed(text):
        """解析随机种子 - 留空返回None（随机），纯数字转换为整数"""
        text = text.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return text

    def _check_project_selected(self):
        """检查是否选择了项目"""
        if not hasattr(self.main_window, 'current_project_name') or not self.main_window.current_project_name:
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                                self.main_window.tr("请先选择一个项目！"))
            return False
        return True
