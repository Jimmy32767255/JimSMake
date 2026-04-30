import os
import json
import sys
import shutil
import zipfile
import tarfile
from loguru import logger
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QComboBox, QProgressDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ExportWorker(QThread):
    """导出工作线程"""
    progress_updated = pyqtSignal(int)
    file_processed = pyqtSignal(str)
    export_finished = pyqtSignal(bool, str)
    
    def __init__(self, source_dir, output_path, export_type="project"):
        super().__init__()
        self.source_dir = source_dir
        self.output_path = output_path
        self.export_type = export_type
        self.is_cancelled = False
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        try:
            if self.output_path.endswith('.zip'):
                self._compress_to_zip()
            elif self.output_path.endswith('.tar.xz'):
                self._compress_to_tar_xz()
            else:
                self.output_path += '.zip'
                self._compress_to_zip()
                
            if not self.is_cancelled:
                self.export_finished.emit(True, self.output_path)
            else:
                # 删除未完成的文件
                if os.path.exists(self.output_path):
                    os.remove(self.output_path)
                self.export_finished.emit(False, "导出已取消")
                
        except Exception as e:
            logger.error(f"导出失败: {e}")
            # 删除未完成的文件
            if os.path.exists(self.output_path):
                os.remove(self.output_path)
            self.export_finished.emit(False, str(e))
    
    def _compress_to_zip(self):
        """将目录压缩为ZIP文件，包含顶级目录名"""
        # 获取所有文件列表
        all_files = []
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)

        total_files = len(all_files)

        with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i, file_path in enumerate(all_files):
                if self.is_cancelled:
                    return

                # 包含顶级目录名的路径
                arcname = os.path.relpath(file_path, os.path.dirname(self.source_dir))
                zipf.write(file_path, arcname)

                # 更新进度
                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)
                self.file_processed.emit(arcname)

    def _compress_to_tar_xz(self):
        """将目录压缩为TAR.XZ文件，包含顶级目录名"""
        # 获取所有文件列表
        all_files = []
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)

        total_files = len(all_files)

        with tarfile.open(self.output_path, "w:xz") as tar:
            for i, file_path in enumerate(all_files):
                if self.is_cancelled:
                    return

                # 包含顶级目录名的路径
                arcname = os.path.relpath(file_path, os.path.dirname(self.source_dir))
                tar.add(file_path, arcname)

                # 更新进度
                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)
                self.file_processed.emit(arcname)


class ProjectManager:
    """项目管理工具类"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def get_project_base_dir(self):
        """获取项目基础目录"""
        is_appimage = os.environ.get('APPIMAGE') is not None
        is_pyinstaller = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        
        if is_appimage:
            cwd = os.getcwd()
            project_dir = os.path.join(cwd, "Project")
            logger.debug(f"AppImage 模式项目目录: {project_dir}")
            return project_dir
        elif is_pyinstaller:
            exe_dir = os.path.dirname(sys.executable)
            project_dir = os.path.join(exe_dir, "Project")
            logger.debug(f"PyInstaller 模式项目目录: {project_dir}")
            return project_dir
        else:
            project_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Project")
            logger.debug(f"开发模式项目目录: {project_dir}")
            return project_dir

    def get_current_project_dir(self):
        """获取当前项目目录"""
        if hasattr(self.main_window, 'current_project_name') and self.main_window.current_project_name:
            if hasattr(self.main_window, 'current_project_group') and self.main_window.current_project_group:
                project_dir = os.path.join(self.get_project_base_dir(), self.main_window.current_project_group, 
                                         self.main_window.current_project_name)
            else:
                project_dir = os.path.join(self.get_project_base_dir(), self.main_window.current_project_name)
            logger.debug(f"获取当前项目目录: {project_dir}")
            logger.debug(f"项目目录绝对路径: {os.path.abspath(project_dir)}")
            logger.debug(f"项目目录是否存在: {os.path.exists(project_dir)}")
            return project_dir
        logger.debug("没有当前项目，返回None")
        return None

    def get_current_project_group_dir(self):
        """获取当前项目组目录"""
        if hasattr(self.main_window, 'current_project_group') and self.main_window.current_project_group:
            group_dir = os.path.join(self.get_project_base_dir(), self.main_window.current_project_group)
            logger.debug(f"获取当前项目组目录: {group_dir}")
            return group_dir
        return self.get_project_base_dir()

    def load_project_config(self, project_dir):
        """加载项目配置文件"""
        if not project_dir:
            logger.warning("项目目录为空，无法加载配置")
            self._set_default_config()
            return

        config_path = os.path.join(project_dir, "config.json")
        logger.debug(f"尝试加载项目配置: {config_path}")

        if not os.path.exists(config_path):
            logger.info(f"项目配置文件不存在，使用默认配置: {config_path}")
            self._set_default_config()
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 加载元数据
            metadata = config.get('metadata', {})
            if hasattr(self.main_window, 'metadata_title') and self.main_window.metadata_title is not None:
                self.main_window.metadata_title.setText(metadata.get('title', ''))
            if hasattr(self.main_window, 'metadata_author') and self.main_window.metadata_author is not None:
                self.main_window.metadata_author.setText(metadata.get('author', ''))

            # 加载肯定语设置
            affirmation = config.get('affirmation', {})
            self._load_text_setting('affirmation_file', affirmation.get('file'), project_dir)
            self._load_text_setting('affirmation_text', affirmation.get('text'))
            self._load_text_setting('text_file', affirmation.get('text_file'), project_dir)
            self._load_combo_setting('tts_engine', affirmation.get('tts_engine'))
            self._load_slider_setting('affirmation_volume', affirmation.get('volume'))
            self._load_spin_setting('affirmation_volume_spin', affirmation.get('volume'))
            self._load_combo_setting('frequency_mode', affirmation.get('frequency_mode'))
            self._load_slider_setting('speed_slider', affirmation.get('speed'))
            self._load_spin_setting('speed_spin', affirmation.get('speed'))
            self._load_checkbox_setting('reverse_check', affirmation.get('reverse'))

            # 加载叠加设置
            overlay = config.get('overlay', {})
            self._load_spin_setting('overlay_times', overlay.get('times'))
            self._load_spin_setting('overlay_interval', overlay.get('interval'))
            self._load_spin_setting('volume_decrease', overlay.get('volume_decrease'))

            # 加载背景音设置
            background = config.get('background', {})
            self._load_text_setting('background_file', background.get('file'), project_dir)
            self._load_slider_setting('background_volume', background.get('volume'))
            self._load_spin_setting('background_volume_spin', background.get('volume'))

            # 加载特定频率音轨设置
            freq_track = config.get('freq_track', {})
            self._load_checkbox_setting('freq_track_enabled', freq_track.get('enabled'))
            self._load_text_setting('freq_track_freq', freq_track.get('frequency'))
            self._load_spin_setting('freq_track_volume', freq_track.get('volume'))

            # 加载输出设置
            output = config.get('output', {})
            self._load_checkbox_setting('generate_audio', output.get('generate_audio'))
            self._load_checkbox_setting('generate_video', output.get('generate_video'))
            self._load_combo_setting('audio_format', output.get('audio_format'))
            self._load_combo_setting('audio_sample_rate', output.get('audio_sample_rate'))
            self._load_text_setting('video_image', output.get('video_image'), project_dir)
            self._load_text_setting('search_keyword', output.get('search_keyword'))
            self._load_combo_setting('search_engine', output.get('search_engine'))
            self._load_combo_setting('video_format', output.get('video_format'))
            self._load_combo_setting('video_audio_sample_rate', output.get('video_audio_sample_rate'))
            self._load_combo_setting('video_bitrate', output.get('video_bitrate'))
            self._load_combo_setting('video_resolution', output.get('video_resolution'))

            # 加载完整性检查设置
            self._load_checkbox_setting('ensure_integrity_check', config.get('ensure_integrity'))

            logger.info(f"项目配置加载成功: {config_path}")
            logger.debug(f"配置内容: {config}")

        except json.JSONDecodeError as e:
            logger.error(f"项目配置文件格式错误: {config_path}, 错误: {e}")
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr(f"项目配置文件格式错误，将使用默认配置。"))
            # 删除损坏的配置文件并创建新的默认配置
            self._reset_corrupted_config(project_dir, config_path)
        except Exception as e:
            logger.error(f"加载项目配置失败: {config_path}, 错误: {e}")
            self._set_default_config()

    def _set_default_config(self):
        """设置默认配置 - 重置所有 UI 控件到默认值"""
        # 元数据
        if hasattr(self.main_window, 'metadata_title') and self.main_window.metadata_title is not None:
            self.main_window.metadata_title.clear()
        if hasattr(self.main_window, 'metadata_author') and self.main_window.metadata_author is not None:
            self.main_window.metadata_author.clear()

        # 肯定语设置
        if hasattr(self.main_window, 'affirmation_file') and self.main_window.affirmation_file is not None:
            self.main_window.affirmation_file.clear()
        if hasattr(self.main_window, 'affirmation_text') and self.main_window.affirmation_text is not None:
            self.main_window.affirmation_text.clear()
        if hasattr(self.main_window, 'text_file') and self.main_window.text_file is not None:
            self.main_window.text_file.clear()
        if hasattr(self.main_window, 'tts_engine') and self.main_window.tts_engine is not None:
            self.main_window.tts_engine.setCurrentIndex(0)
        if hasattr(self.main_window, 'affirmation_volume') and self.main_window.affirmation_volume is not None:
            self.main_window.affirmation_volume.setValue(-230)
        if hasattr(self.main_window, 'affirmation_volume_spin') and self.main_window.affirmation_volume_spin is not None:
            self.main_window.affirmation_volume_spin.setValue(-23.0)
        if hasattr(self.main_window, 'frequency_mode') and self.main_window.frequency_mode is not None:
            self.main_window.frequency_mode.setCurrentIndex(0)
        if hasattr(self.main_window, 'speed_slider') and self.main_window.speed_slider is not None:
            self.main_window.speed_slider.setValue(10)
        if hasattr(self.main_window, 'speed_spin') and self.main_window.speed_spin is not None:
            self.main_window.speed_spin.setValue(1.0)
        if hasattr(self.main_window, 'reverse_check') and self.main_window.reverse_check is not None:
            self.main_window.reverse_check.setChecked(False)

        # 叠加设置
        if hasattr(self.main_window, 'overlay_times') and self.main_window.overlay_times is not None:
            self.main_window.overlay_times.setValue(1)
        if hasattr(self.main_window, 'overlay_interval') and self.main_window.overlay_interval is not None:
            self.main_window.overlay_interval.setValue(1.0)
        if hasattr(self.main_window, 'volume_decrease') and self.main_window.volume_decrease is not None:
            self.main_window.volume_decrease.setValue(0.0)

        # 背景音设置
        if hasattr(self.main_window, 'background_file') and self.main_window.background_file is not None:
            self.main_window.background_file.clear()
        if hasattr(self.main_window, 'background_volume') and self.main_window.background_volume is not None:
            self.main_window.background_volume.setValue(0)
        if hasattr(self.main_window, 'background_volume_spin') and self.main_window.background_volume_spin is not None:
            self.main_window.background_volume_spin.setValue(0.0)

        # 特定频率音轨设置
        if hasattr(self.main_window, 'freq_track_enabled') and self.main_window.freq_track_enabled is not None:
            self.main_window.freq_track_enabled.setChecked(False)
        if hasattr(self.main_window, 'freq_track_freq') and self.main_window.freq_track_freq is not None:
            self.main_window.freq_track_freq.setText("432")
        if hasattr(self.main_window, 'freq_track_volume') and self.main_window.freq_track_volume is not None:
            self.main_window.freq_track_volume.setValue(-23.0)

        # 输出设置
        if hasattr(self.main_window, 'generate_audio') and self.main_window.generate_audio is not None:
            self.main_window.generate_audio.setChecked(True)
        if hasattr(self.main_window, 'generate_video') and self.main_window.generate_video is not None:
            self.main_window.generate_video.setChecked(False)
        if hasattr(self.main_window, 'audio_format') and self.main_window.audio_format is not None:
            self.main_window.audio_format.setCurrentIndex(0)
        if hasattr(self.main_window, 'audio_sample_rate') and self.main_window.audio_sample_rate is not None:
            self.main_window.audio_sample_rate.setCurrentIndex(0)
        if hasattr(self.main_window, 'video_image') and self.main_window.video_image is not None:
            self.main_window.video_image.clear()
        if hasattr(self.main_window, 'search_keyword') and self.main_window.search_keyword is not None:
            self.main_window.search_keyword.clear()
        if hasattr(self.main_window, 'search_engine') and self.main_window.search_engine is not None:
            self.main_window.search_engine.setCurrentIndex(0)
        if hasattr(self.main_window, 'video_format') and self.main_window.video_format is not None:
            self.main_window.video_format.setCurrentIndex(0)
        if hasattr(self.main_window, 'video_audio_sample_rate') and self.main_window.video_audio_sample_rate is not None:
            self.main_window.video_audio_sample_rate.setCurrentIndex(0)
        if hasattr(self.main_window, 'video_bitrate') and self.main_window.video_bitrate is not None:
            self.main_window.video_bitrate.setCurrentIndex(0)
        if hasattr(self.main_window, 'video_resolution') and self.main_window.video_resolution is not None:
            self.main_window.video_resolution.setCurrentIndex(0)

        # 完整性检查设置
        if hasattr(self.main_window, 'ensure_integrity_check') and self.main_window.ensure_integrity_check is not None:
            self.main_window.ensure_integrity_check.setChecked(False)

    def _reset_corrupted_config(self, project_dir, config_path):
        """重置损坏的配置文件 - 删除旧文件并创建新的默认配置"""
        try:
            # 先重置 UI 到默认值
            self._set_default_config()

            # 删除损坏的配置文件
            if os.path.exists(config_path):
                os.remove(config_path)
                logger.info(f"已删除损坏的配置文件: {config_path}")

            # 创建新的默认配置文件
            if project_dir and os.path.exists(project_dir):
                self._create_default_config_file(project_dir, config_path)

        except Exception as e:
            logger.error(f"重置损坏的配置文件失败: {e}")

    def _create_default_config_file(self, project_dir, config_path):
        """创建默认配置文件"""
        try:
            default_config = {
                "version": "1.0",
                "metadata": {
                    "title": "",
                    "author": ""
                },
                "affirmation": {
                    "file": "",
                    "text": "",
                    "text_file": "",
                    "tts_engine": "",
                    "volume": -23.0,
                    "frequency_mode": "",
                    "speed": 1.0,
                    "reverse": False
                },
                "overlay": {
                    "times": 1,
                    "interval": 1.0,
                    "volume_decrease": 0.0
                },
                "background": {
                    "file": "",
                    "volume": 0.0
                },
                "freq_track": {
                    "enabled": False,
                    "frequency": "432",
                    "volume": -23.0
                },
                "output": {
                    "generate_audio": True,
                    "generate_video": False,
                    "audio_format": "",
                    "audio_sample_rate": "",
                    "video_image": "",
                    "search_keyword": "",
                    "search_engine": "",
                    "video_format": "",
                    "video_audio_sample_rate": "",
                    "video_bitrate": "",
                    "video_resolution": ""
                },
                "ensure_integrity": False
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)

            logger.info(f"已创建新的默认配置文件: {config_path}")

        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")

    def _load_text_setting(self, attr_name, value, project_dir=None):
        """加载文本设置"""
        if value is None:
            return
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                # 如果是文件路径，检查文件是否存在
                if project_dir and value:
                    if not os.path.isabs(value):
                        # 相对路径，相对于项目目录
                        abs_path = os.path.join(project_dir, value)
                    else:
                        abs_path = value
                    if os.path.exists(abs_path):
                        widget.setText(abs_path)
                    else:
                        # 文件不存在，尝试自动检测（保留空值或触发自动检测逻辑）
                        logger.warning(f"配置文件中的文件不存在: {value}")
                        widget.clear()
                else:
                    widget.setText(value)

    def _load_combo_setting(self, attr_name, value):
        """加载下拉框设置"""
        if value is None:
            return
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                index = widget.findText(value)
                if index >= 0:
                    widget.setCurrentIndex(index)

    def _load_slider_setting(self, attr_name, value):
        """加载滑块设置"""
        if value is None:
            return
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                widget.setValue(int(value))

    def _load_spin_setting(self, attr_name, value):
        """加载数值框设置"""
        if value is None:
            return
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                widget.setValue(value)

    def _load_checkbox_setting(self, attr_name, value):
        """加载复选框设置"""
        if value is None:
            return
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                widget.setChecked(value)

    def save_project_config(self, project_dir):
        """保存项目配置文件"""
        config_path = os.path.join(project_dir, "config.json")
        logger.debug(f"保存项目配置: {config_path}")

        try:
            config = {
                "version": "1.0",
                "metadata": {
                    "title": self._get_text_value('metadata_title'),
                    "author": self._get_text_value('metadata_author')
                },
                "affirmation": {
                    "file": self._get_relative_path('affirmation_file', project_dir),
                    "text": self._get_text_value('affirmation_text'),
                    "text_file": self._get_relative_path('text_file', project_dir),
                    "tts_engine": self._get_combo_value('tts_engine'),
                    "volume": self._get_spin_value('affirmation_volume_spin'),
                    "frequency_mode": self._get_combo_value('frequency_mode'),
                    "speed": self._get_spin_value('speed_spin'),
                    "reverse": self._get_checkbox_value('reverse_check')
                },
                "overlay": {
                    "times": self._get_spin_value('overlay_times'),
                    "interval": self._get_spin_value('overlay_interval'),
                    "volume_decrease": self._get_spin_value('volume_decrease')
                },
                "background": {
                    "file": self._get_relative_path('background_file', project_dir),
                    "volume": self._get_spin_value('background_volume_spin')
                },
                "freq_track": {
                    "enabled": self._get_checkbox_value('freq_track_enabled'),
                    "frequency": self._get_text_value('freq_track_freq'),
                    "volume": self._get_spin_value('freq_track_volume')
                },
                "output": {
                    "generate_audio": self._get_checkbox_value('generate_audio'),
                    "generate_video": self._get_checkbox_value('generate_video'),
                    "audio_format": self._get_combo_value('audio_format'),
                    "audio_sample_rate": self._get_combo_value('audio_sample_rate'),
                    "video_image": self._get_relative_path('video_image', project_dir),
                    "search_keyword": self._get_text_value('search_keyword'),
                    "search_engine": self._get_combo_value('search_engine'),
                    "video_format": self._get_combo_value('video_format'),
                    "video_audio_sample_rate": self._get_combo_value('video_audio_sample_rate'),
                    "video_bitrate": self._get_combo_value('video_bitrate'),
                    "video_resolution": self._get_combo_value('video_resolution')
                },
                "ensure_integrity": self._get_checkbox_value('ensure_integrity_check')
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info(f"项目配置保存成功: {config_path}")

        except Exception as e:
            logger.error(f"保存项目配置失败: {config_path}, 错误: {e}")

    def _get_text_value(self, attr_name):
        """获取文本控件值"""
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                return widget.text()
        return ""

    def _get_combo_value(self, attr_name):
        """获取下拉框控件值"""
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                return widget.currentText()
        return ""

    def _get_spin_value(self, attr_name):
        """获取数值框控件值"""
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                return widget.value()
        return 0

    def _get_checkbox_value(self, attr_name):
        """获取复选框控件值"""
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                return widget.isChecked()
        return False

    def _get_relative_path(self, attr_name, project_dir):
        """获取相对路径（如果路径在项目目录内）"""
        if hasattr(self.main_window, attr_name):
            widget = getattr(self.main_window, attr_name)
            if widget is not None:
                path = widget.text()
                if path and os.path.isabs(path):
                    try:
                        # 尝试转换为相对路径
                        rel_path = os.path.relpath(path, project_dir)
                        # 如果相对路径不以 .. 开头，说明在项目目录内
                        if not rel_path.startswith('..'):
                            return rel_path
                    except ValueError:
                        pass
                return path
        return ""

    def _compress_to_zip(self, source_dir, output_path):
        """将目录压缩为ZIP文件，包含顶级目录名"""
        import zipfile

        logger.debug(f"开始压缩为ZIP: {source_dir} -> {output_path}")
        
        # 获取顶级目录名
        top_dir_name = os.path.basename(os.path.normpath(source_dir))

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 包含顶级目录名的路径
                    rel_path = os.path.relpath(file_path, os.path.dirname(source_dir))
                    zipf.write(file_path, rel_path)
                    logger.debug(f"添加文件到ZIP: {rel_path}")

        logger.info(f"ZIP压缩完成: {output_path}")

    def _compress_to_tar_xz(self, source_dir, output_path):
        """将目录压缩为TAR.XZ文件"""
        import tarfile

        logger.debug(f"开始压缩为TAR.XZ: {source_dir} -> {output_path}")

        with tarfile.open(output_path, "w:xz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

        logger.info(f"TAR.XZ压缩完成: {output_path}")

    def export_project(self, project_dir, output_path):
        """导出项目"""
        logger.info(f"开始导出项目: {project_dir} -> {output_path}")

        try:
            if output_path.endswith('.zip'):
                self._compress_to_zip(project_dir, output_path)
            elif output_path.endswith('.tar.xz'):
                self._compress_to_tar_xz(project_dir, output_path)
            else:
                output_path += '.zip'
                self._compress_to_zip(project_dir, output_path)

            logger.info(f"项目导出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出项目失败: {e}")
            return False

    def export_project_group(self, group_dir, output_path):
        """导出项目组"""
        logger.info(f"开始导出项目组: {group_dir} -> {output_path}")

        try:
            if output_path.endswith('.zip'):
                self._compress_to_zip(group_dir, output_path)
            elif output_path.endswith('.tar.xz'):
                self._compress_to_tar_xz(group_dir, output_path)
            else:
                output_path += '.zip'
                self._compress_to_zip(group_dir, output_path)

            logger.info(f"项目组导出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出项目组失败: {e}")
            return False

    def _detect_import_type(self, file_path):
        """检测导入文件类型（项目还是项目组）"""
        logger.debug(f"检测导入类型: {file_path}")

        try:
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zf:
                    file_list = zf.namelist()
            elif file_path.endswith('.tar.xz'):
                with tarfile.open(file_path, 'r:xz') as tf:
                    file_list = [m.name for m in tf.getmembers()]
            else:
                return "unknown"

            logger.debug(f"压缩包文件列表: {file_list[:10]}...")  # 只显示前10个

            top_dirs = set()
            for name in file_list:
                parts = name.split('/')
                if len(parts) > 0 and parts[0]:
                    top_dirs.add(parts[0])

            logger.debug(f"顶级目录: {top_dirs}")

            if len(top_dirs) == 1:
                top_dir = list(top_dirs)[0]
                
                # 检查是否为项目：在顶级目录下查找 config.json 和 Assets 目录
                # 文件路径格式: 顶级目录/config.json 或 顶级目录/Assets/xxx
                has_config = any(f.startswith(f'{top_dir}/config.json') for f in file_list)
                has_assets = any(f.startswith(f'{top_dir}/Assets/') for f in file_list)
                
                logger.debug(f"项目检测: has_config={has_config}, has_assets={has_assets}")

                if has_config and has_assets:
                    logger.debug(f"检测到项目类型")
                    return "project"

                # 检查是否为项目组：查找二级目录下的项目结构
                subdirs = set()
                for name in file_list:
                    parts = name.split('/')
                    if len(parts) > 1 and parts[1] and not parts[1].startswith('.'):
                        subdirs.add(parts[1])

                logger.debug(f"二级目录: {subdirs}")

                # 检查组内是否有项目结构
                if len(subdirs) > 0:
                    # 检查任意子目录是否包含项目特征文件
                    for subdir in subdirs:
                        subdir_has_config = any(f.startswith(f'{top_dir}/{subdir}/config.json') for f in file_list)
                        subdir_has_assets = any(f.startswith(f'{top_dir}/{subdir}/Assets/') for f in file_list)
                        logger.debug(f"子目录 {subdir}: has_config={subdir_has_config}, has_assets={subdir_has_assets}")
                        if subdir_has_config and subdir_has_assets:
                            logger.debug(f"检测到项目组类型")
                            return "group"

            return "unknown"

        except Exception as e:
            logger.error(f"检测导入类型失败: {e}")
            return "unknown"

    def _extract_zip(self, file_path, target_dir):
        """解压ZIP文件"""
        import zipfile

        logger.debug(f"解压ZIP: {file_path} -> {target_dir}")

        with zipfile.ZipFile(file_path, 'r') as zipf:
            zipf.extractall(target_dir)

        logger.info(f"ZIP解压完成")

    def _extract_tar_xz(self, file_path, target_dir):
        """解压TAR.XZ文件"""
        import tarfile

        logger.debug(f"解压TAR.XZ: {file_path} -> {target_dir}")

        with tarfile.open(file_path, 'r:xz') as tar:
            tar.extractall(target_dir)

        logger.info(f"TAR.XZ解压完成")

    def _get_archive_top_dir(self, file_path):
        """获取压缩包的顶级目录名"""
        try:
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zf:
                    file_list = zf.namelist()
            elif file_path.endswith('.tar.xz'):
                with tarfile.open(file_path, 'r:xz') as tf:
                    file_list = [m.name for m in tf.getmembers()]
            else:
                return None

            # 获取所有顶级目录
            top_dirs = set()
            for name in file_list:
                parts = name.split('/')
                if len(parts) > 0 and parts[0]:
                    top_dirs.add(parts[0])

            # 如果只有一个顶级目录，返回它
            if len(top_dirs) == 1:
                return list(top_dirs)[0]
            return None
        except Exception as e:
            logger.error(f"获取压缩包顶级目录失败: {e}")
            return None

    def _extract_zip_to_dir(self, file_path, target_dir):
        """将ZIP文件解压到指定目录，去掉顶级目录层级"""
        logger.debug(f"解压ZIP到目录: {file_path} -> {target_dir}")

        with zipfile.ZipFile(file_path, 'r') as zipf:
            for member in zipf.namelist():
                # 去掉顶级目录
                parts = member.split('/')
                if len(parts) > 1:
                    # 重新组合路径（去掉第一个元素）
                    target_path = os.path.join(target_dir, '/'.join(parts[1:]))
                else:
                    # 跳过顶级目录本身
                    continue

                # 创建目录或解压文件
                if member.endswith('/'):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zipf.open(member) as source, open(target_path, 'wb') as target:
                        target.write(source.read())

        logger.info(f"ZIP解压完成")

    def _extract_tar_xz_to_dir(self, file_path, target_dir):
        """将TAR.XZ文件解压到指定目录，去掉顶级目录层级"""
        logger.debug(f"解压TAR.XZ到目录: {file_path} -> {target_dir}")

        with tarfile.open(file_path, 'r:xz') as tar:
            for member in tar.getmembers():
                # 去掉顶级目录
                parts = member.name.split('/')
                if len(parts) > 1:
                    # 重新组合路径（去掉第一个元素）
                    target_path = os.path.join(target_dir, '/'.join(parts[1:]))
                else:
                    # 跳过顶级目录本身
                    continue

                # 创建目录或解压文件
                if member.isdir():
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with tar.extractfile(member) as source, open(target_path, 'wb') as target:
                        target.write(source.read())

        logger.info(f"TAR.XZ解压完成")

    def import_project_or_group(self, file_path):
        """导入项目或项目组"""
        logger.info(f"开始导入: {file_path}")

        try:
            import_type = self._detect_import_type(file_path)

            if import_type == "project":
                self._import_project(file_path)
            elif import_type == "group":
                self._import_project_group(file_path)
            else:
                from PyQt5.QtWidgets import QMessageBox
                msg_box = QMessageBox(self.main_window)
                msg_box.setWindowTitle(self.main_window.tr("选择导入类型"))
                msg_box.setText(self.main_window.tr("无法自动检测导入类型。请选择要导入为项目还是项目组？"))
                project_btn = msg_box.addButton(self.main_window.tr("项目"), QMessageBox.ActionRole)
                group_btn = msg_box.addButton(self.main_window.tr("项目组"), QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Cancel)
                msg_box.exec_()
                
                if msg_box.clickedButton() == project_btn:
                    self._import_project(file_path)
                elif msg_box.clickedButton() == group_btn:
                    self._import_project_group(file_path)

        except Exception as e:
            logger.error(f"导入失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"导入失败: {str(e)}"))

    def _import_project(self, file_path):
        """导入项目"""
        logger.info(f"开始导入项目: {file_path}")

        if not self.main_window.current_project_group:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目组来导入项目！"))
            return

        # 获取压缩包中的项目名（顶级目录名）
        project_name = self._get_archive_top_dir(file_path)
        if not project_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("无法识别压缩包中的项目结构！"))
            return

        # 检查目标项目是否已存在
        target_dir = self.get_current_project_group_dir()
        project_path = os.path.join(target_dir, project_name)
        
        if os.path.exists(project_path):
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self.main_window,
                self.main_window.tr("项目已存在"),
                self.main_window.tr(f"项目 '{project_name}' 已存在，是否覆盖？"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            # 删除旧项目
            import shutil
            shutil.rmtree(project_path)

        # 创建项目目录并解压
        os.makedirs(project_path, exist_ok=True)

        if file_path.endswith('.zip'):
            self._extract_zip_to_dir(file_path, project_path)
        elif file_path.endswith('.tar.xz'):
            self._extract_tar_xz_to_dir(file_path, project_path)

        logger.info(f"项目导入成功到: {project_path}")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                               self.main_window.tr(f"项目 '{project_name}' 导入成功！"))

        self.refresh_project_list()
        # 自动选中新导入的项目
        index = self.main_window.project_list.findData(project_name)
        if index >= 0:
            self.main_window.project_list.setCurrentIndex(index)

    def _import_project_group(self, file_path):
        """导入项目组"""
        logger.info(f"开始导入项目组: {file_path}")

        # 获取压缩包中的项目组名（顶级目录名）
        group_name = self._get_archive_top_dir(file_path)
        if not group_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("无法识别压缩包中的项目组结构！"))
            return

        # 检查目标项目组是否已存在
        target_dir = self.get_project_base_dir()
        group_path = os.path.join(target_dir, group_name)
        
        if os.path.exists(group_path):
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self.main_window,
                self.main_window.tr("项目组已存在"),
                self.main_window.tr(f"项目组 '{group_name}' 已存在，是否覆盖？"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            # 删除旧项目组
            import shutil
            shutil.rmtree(group_path)

        # 创建项目组目录并解压
        os.makedirs(group_path, exist_ok=True)

        if file_path.endswith('.zip'):
            self._extract_zip_to_dir(file_path, group_path)
        elif file_path.endswith('.tar.xz'):
            self._extract_tar_xz_to_dir(file_path, group_path)

        logger.info(f"项目组导入成功到: {group_path}")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                               self.main_window.tr(f"项目组 '{group_name}' 导入成功！"))

        self.refresh_project_group_list()
        # 自动选中新导入的项目组
        index = self.main_window.project_group_list.findData(group_name)
        if index >= 0:
            self.main_window.project_group_list.setCurrentIndex(index)

    def refresh_project_group_list(self):
        """刷新项目组列表"""
        logger.debug("刷新项目组列表")
        self.main_window.project_group_list.clear()

        project_base = self.get_project_base_dir()
        if not os.path.exists(project_base):
            os.makedirs(project_base)
            logger.debug(f"创建项目基础目录: {project_base}")

        groups = []
        try:
            for item in os.listdir(project_base):
                item_path = os.path.join(project_base, item)
                if os.path.isdir(item_path):
                    groups.append(item)
        except Exception as e:
            logger.error(f"读取项目组列表失败: {e}")

        if not groups:
            default_group = self.main_window.tr("默认项目组")
            default_group_path = os.path.join(project_base, default_group)
            try:
                os.makedirs(default_group_path)
                groups.append(default_group)
                logger.info(f"创建默认项目组: {default_group}")
            except Exception as e:
                logger.error(f"创建默认项目组失败: {e}")

        self.main_window.project_group_list.addItem(self.main_window.tr("-- 选择项目组 --"), "")
        for group in sorted(groups):
            self.main_window.project_group_list.addItem(group, group)

        if hasattr(self.main_window, 'current_project_group') and self.main_window.current_project_group:
            index = self.main_window.project_group_list.findData(self.main_window.current_project_group)
            if index >= 0:
                self.main_window.project_group_list.setCurrentIndex(index)
                self.refresh_project_list()

        logger.info(f"项目组列表刷新完成，共 {len(groups)} 个项目组")

    def on_project_group_selected(self, index):
        """项目组选择改变"""
        group_name = self.main_window.project_group_list.itemData(index)
        if group_name:
            self.switch_project_group(group_name)

    def switch_project_group(self, group_name):
        """切换到指定项目组"""
        logger.info(f"切换到项目组: {group_name}")
        self.main_window.current_project_group = group_name
        self.main_window.current_project_group_label.setText(group_name)

        self.main_window.settings.setValue("current_project_group", group_name)
        self.refresh_project_list()

        logger.info(f"已切换到项目组: {group_name}")

    def create_new_project_group(self):
        """创建新项目组"""
        group_name = self.main_window.new_project_group_name.text().strip()

        if not group_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请输入项目组名称！"))
            return

        import re
        if not re.match(r'^[\w\-\s]+$', group_name):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("项目组名称只能包含字母、数字、下划线、横线和空格！"))
            return

        project_base = self.get_project_base_dir()
        group_dir = os.path.join(project_base, group_name)

        if os.path.exists(group_dir):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr(f"项目组 '{group_name}' 已存在！"))
            return

        try:
            os.makedirs(group_dir)

            logger.info(f"项目组创建成功: {group_name}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"项目组 '{group_name}' 创建成功！"))

            self.main_window.new_project_group_name.clear()

            self.refresh_project_group_list()
            index = self.main_window.project_group_list.findData(group_name)
            if index >= 0:
                self.main_window.project_group_list.setCurrentIndex(index)

        except Exception as e:
            logger.error(f"创建项目组失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"创建项目组失败: {str(e)}"))

    def delete_project_group(self):
        """删除项目组"""
        group_name = self.main_window.project_group_list.currentData()

        if not group_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目组！"))
            return

        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self.main_window, self.main_window.tr("确认删除"),
                                    self.main_window.tr(f"确定要删除项目组 '{group_name}' 吗？\n")
                                    + self.main_window.tr("此操作将删除项目组下的所有项目，且不可恢复！"),
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        try:
            group_dir = os.path.join(self.get_project_base_dir(), group_name)
            import shutil
            shutil.rmtree(group_dir)

            logger.info(f"项目组删除成功: {group_name}")
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"项目组 '{group_name}' 已删除！"))

            if self.main_window.current_project_group == group_name:
                self.main_window.current_project_group = None
                self.main_window.current_project_group_label.setText(self.main_window.tr("未选择项目组"))
                self.main_window.settings.remove("current_project_group")
                self.main_window.current_project_name = None
                self.main_window.current_project_label.setText(self.main_window.tr("未选择项目"))
                self.main_window.settings.remove("current_project")

            self.refresh_project_group_list()

        except Exception as e:
            logger.error(f"删除项目组失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"删除项目组失败: {str(e)}"))

    def refresh_project_list(self):
        """刷新项目列表"""
        logger.debug("刷新项目列表")
        self.main_window.project_list.clear()

        if hasattr(self.main_window, 'current_project_group') and self.main_window.current_project_group:
            project_base = self.get_current_project_group_dir()
        else:
            project_base = self.get_project_base_dir()

        if not os.path.exists(project_base):
            os.makedirs(project_base)
            logger.debug(f"创建项目目录: {project_base}")

        projects = []
        try:
            for item in os.listdir(project_base):
                item_path = os.path.join(project_base, item)
                if os.path.isdir(item_path):
                    projects.append(item)
        except Exception as e:
            logger.error(f"读取项目列表失败: {e}")

        self.main_window.project_list.addItem(self.main_window.tr("-- 选择项目 --"), "")
        for project in sorted(projects):
            self.main_window.project_list.addItem(project, project)

        if hasattr(self.main_window, 'current_project_name') and self.main_window.current_project_name:
            index = self.main_window.project_list.findData(self.main_window.current_project_name)
            if index >= 0:
                self.main_window.project_list.setCurrentIndex(index)

        logger.info(f"项目列表刷新完成，共 {len(projects)} 个项目")

    def on_project_selected(self, index):
        """项目选择改变"""
        project_name = self.main_window.project_list.itemData(index)
        if project_name:
            self.switch_project(project_name)

    def switch_project(self, project_name):
        """切换到指定项目"""
        logger.info(f"切换到项目: {project_name}")
        self.main_window.current_project_name = project_name
        self.main_window.current_project_label.setText(project_name)

        project_dir = self.get_current_project_dir()
        if project_dir:
            self.main_window.project_path_label.setText(project_dir)
            self.load_project_resources(project_dir)

        self.main_window.settings.setValue("current_project", project_name)

        logger.info(f"已切换到项目: {project_name}")

    def load_project_resources(self, project_dir):
        """自动加载项目中的资源文件"""
        if not project_dir or not os.path.exists(project_dir):
            logger.debug(f"项目目录不存在: {project_dir}")
            return

        logger.info(f"加载项目资源: {project_dir}")
        logger.debug(f"项目目录绝对路径: {os.path.abspath(project_dir)}")

        self.load_project_config(project_dir)

        assets_dir = os.path.join(project_dir, "Assets")
        affirmation_dir = os.path.join(assets_dir, "Affirmation")

        logger.debug(f"Assets目录: {assets_dir}, 是否存在: {os.path.exists(assets_dir)}")
        logger.debug(f"Affirmation目录: {affirmation_dir}, 是否存在: {os.path.exists(affirmation_dir)}")

        if hasattr(self.main_window, 'text_file') and self.main_window.text_file is not None:
            raw_txt_path = os.path.join(affirmation_dir, "Raw.txt")
            logger.debug(f"查找文本文件: {raw_txt_path}, 是否存在: {os.path.exists(raw_txt_path)}")
            if os.path.exists(raw_txt_path):
                self.main_window.text_file.setText(raw_txt_path)
                self.main_window.text_sync.load_text_from_file(raw_txt_path)
                logger.info(f"自动加载文本文件: {raw_txt_path}")
            else:
                self.main_window.text_file.clear()
                self.main_window.current_text_file = None
                if hasattr(self.main_window, 'affirmation_text') and self.main_window.affirmation_text is not None:
                    self.main_window.affirmation_text.clear()

        if hasattr(self.main_window, 'affirmation_file') and self.main_window.affirmation_file is not None:
            affirmation_audio = self.find_first_audio_file(affirmation_dir)
            logger.debug(f"查找肯定语音频文件: {affirmation_audio}")
            if affirmation_audio:
                self.main_window.affirmation_file.setText(affirmation_audio)
                logger.info(f"自动加载肯定语音频: {affirmation_audio}")
                logger.debug(f"肯定语音频绝对路径: {os.path.abspath(affirmation_audio)}")
            else:
                self.main_window.affirmation_file.clear()

        if hasattr(self.main_window, 'background_file') and self.main_window.background_file is not None:
            bgm_path = os.path.join(assets_dir, "BGM.wav")
            logger.debug(f"查找背景音乐文件: {bgm_path}, 是否存在: {os.path.exists(bgm_path)}")
            if os.path.exists(bgm_path):
                self.main_window.background_file.setText(bgm_path)
                logger.info(f"自动加载背景音乐: {bgm_path}")
                logger.debug(f"背景音乐绝对路径: {os.path.abspath(bgm_path)}")
            else:
                bg_audio = self.find_first_audio_file(assets_dir, exclude_names=["Raw.txt"])
                logger.debug(f"查找其他背景音乐文件: {bg_audio}")
                if bg_audio and os.path.basename(bg_audio) != "Raw.txt":
                    self.main_window.background_file.setText(bg_audio)
                    logger.info(f"自动加载背景音乐: {bg_audio}")
                    logger.debug(f"背景音乐绝对路径: {os.path.abspath(bg_audio)}")
                else:
                    self.main_window.background_file.clear()

        if hasattr(self.main_window, 'video_image') and self.main_window.video_image is not None:
            viz_path = os.path.join(assets_dir, "Visualization.png")
            logger.debug(f"查找视觉化图片: {viz_path}, 是否存在: {os.path.exists(viz_path)}")
            if os.path.exists(viz_path):
                self.main_window.video_image.setText(viz_path)
                logger.info(f"自动加载视觉化图片: {viz_path}")
                logger.debug(f"视觉化图片绝对路径: {os.path.abspath(viz_path)}")
            else:
                image_file = self.find_first_image_file(assets_dir)
                logger.debug(f"查找其他视觉化图片: {image_file}")
                if image_file:
                    self.main_window.video_image.setText(image_file)
                    logger.info(f"自动加载视觉化图片: {image_file}")
                    logger.debug(f"视觉化图片绝对路径: {os.path.abspath(image_file)}")
                else:
                    self.main_window.video_image.clear()

    def find_first_audio_file(self, directory, exclude_names=None):
        """查找目录中的第一个音频文件"""
        if not directory or not os.path.exists(directory):
            return None

        exclude_names = exclude_names or []
        audio_extensions = ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma']

        try:
            for filename in os.listdir(directory):
                if filename in exclude_names:
                    continue
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in audio_extensions:
                        return file_path
        except Exception as e:
            logger.error(f"查找音频文件失败: {directory}, 错误: {e}")

        return None

    def find_first_image_file(self, directory):
        """查找目录中的第一个图片文件"""
        if not directory or not os.path.exists(directory):
            return None

        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif']

        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in image_extensions:
                        return file_path
        except Exception as e:
            logger.error(f"查找图片文件失败: {directory}, 错误: {e}")

        return None

    def create_project(self):
        """创建新项目"""
        project_name = self.main_window.new_project_name.text().strip()

        if not project_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请输入项目名称！"))
            return

        import re
        if not re.match(r'^[\w\-\s]+$', project_name):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("项目名称只能包含字母、数字、下划线、横线和空格！"))
            return

        if hasattr(self.main_window, 'current_project_group') and self.main_window.current_project_group:
            project_base = self.get_current_project_group_dir()
        else:
            project_base = self.get_project_base_dir()
        project_dir = os.path.join(project_base, project_name)

        if os.path.exists(project_dir):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr(f"项目 '{project_name}' 已存在！"))
            return

        if not hasattr(self.main_window, 'current_project_group') or not self.main_window.current_project_group:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目组！"))
            return

        try:
            os.makedirs(project_dir)
            os.makedirs(os.path.join(project_dir, "Assets", "Affirmation"))
            os.makedirs(os.path.join(project_dir, "Releases", "Audio"))
            os.makedirs(os.path.join(project_dir, "Releases", "Video"))

            readme_path = os.path.join(project_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# {project_name}\n\n")
                f.write(self.main_window.tr("项目描述\n\n"))
                f.write(self.main_window.tr("## 肯定语\n\n"))
                f.write(self.main_window.tr("在此添加肯定语描述...\n\n"))
                f.write(self.main_window.tr("## 背景音乐\n\n"))
                f.write(self.main_window.tr("在此添加背景音乐描述...\n\n"))

            raw_path = os.path.join(project_dir, "Assets", "Affirmation", "Raw.txt")
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(self.main_window.tr("# 在此输入肯定语文本\n"))

            config_path = os.path.join(project_dir, "config.json")
            default_config = {
                "version": "1.0",
                "metadata": {
                    "title": "",
                    "author": ""
                }
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.debug(f"创建默认配置文件: {config_path}")

            logger.info(f"项目创建成功: {project_name}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"项目 '{project_name}' 创建成功！"))

            self.main_window.new_project_name.clear()

            self.refresh_project_list()
            index = self.main_window.project_list.findData(project_name)
            if index >= 0:
                self.main_window.project_list.setCurrentIndex(index)

        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.tr(f"创建项目失败: {str(e)}"))

    def delete_project(self):
        """删除项目"""
        project_name = self.main_window.project_list.currentData()

        if not project_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目！"))
            return

        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self.main_window, self.main_window.tr("确认删除"),
                                    self.main_window.tr(f"确定要删除项目 '{project_name}' 吗？\n")
                                    + self.main_window.tr("此操作不可恢复！"),
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        try:
            project_dir = os.path.join(self.get_current_project_group_dir(), project_name)
            import shutil
            shutil.rmtree(project_dir)

            logger.info(f"项目删除成功: {project_name}")
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"项目 '{project_name}' 已删除！"))

            if self.main_window.current_project_name == project_name:
                self.main_window.current_project_name = None
                self.main_window.current_project_label.setText(self.main_window.tr("未选择项目"))
                self.main_window.project_path_label.setText("./Project/")
                self.main_window.settings.remove("current_project")

            self.refresh_project_list()

        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"删除项目失败: {str(e)}"))

    def copy_project(self):
        """复制项目到当前项目组"""
        project_name = self.main_window.project_list.currentData()

        if not project_name:
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目！"))
            return

        # 输入新项目名称
        new_name, ok = QInputDialog.getText(
            self.main_window,
            self.main_window.tr("复制项目"),
            self.main_window.tr(f"复制项目 '{project_name}'，新项目名称:"),
            text=f"{project_name}_副本"
        )

        if not ok or not new_name:
            return

        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("项目名称不能为空！"))
            return

        import re
        if not re.match(r'^[\w\-\s]+$', new_name):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("项目名称只能包含字母、数字、下划线、横线和空格！"))
            return

        try:
            source_dir = os.path.join(self.get_current_project_group_dir(), project_name)
            target_dir = os.path.join(self.get_current_project_group_dir(), new_name)

            if os.path.exists(target_dir):
                QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                                   self.main_window.tr(f"项目 '{new_name}' 已存在！"))
                return

            shutil.copytree(source_dir, target_dir)

            logger.info(f"项目复制成功: {project_name} -> {new_name}")
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"项目 '{project_name}' 已复制为 '{new_name}'！"))

            self.refresh_project_list()
            index = self.main_window.project_list.findData(new_name)
            if index >= 0:
                self.main_window.project_list.setCurrentIndex(index)

        except Exception as e:
            logger.error(f"复制项目失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"复制项目失败: {str(e)}"))

    def cut_project(self):
        """剪切项目到其他项目组（移动并可选重命名）"""
        project_name = self.main_window.project_list.currentData()

        if not project_name:
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目！"))
            return

        # 获取所有项目组列表
        project_base = self.get_project_base_dir()
        groups = []
        try:
            for item in os.listdir(project_base):
                item_path = os.path.join(project_base, item)
                if os.path.isdir(item_path) and item != self.main_window.current_project_group:
                    groups.append(item)
        except Exception as e:
            logger.error(f"读取项目组列表失败: {e}")

        if not groups:
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("没有其他项目组可以移动！请先创建新的项目组。"))
            return

        # 弹出对话框选择目标项目组
        target_group, ok = QInputDialog.getItem(
            self.main_window,
            self.main_window.tr("剪切项目"),
            self.main_window.tr(f"将项目 '{project_name}' 剪切到:"),
            groups,
            0,
            False
        )

        if not ok or not target_group:
            return

        # 询问是否重命名
        new_name, ok = QInputDialog.getText(
            self.main_window,
            self.main_window.tr("剪切项目"),
            self.main_window.tr("新项目名称（留空保持原名）:"),
            text=project_name
        )

        if not ok:
            return

        new_name = new_name.strip() if new_name else project_name

        if new_name != project_name:
            import re
            if not re.match(r'^[\w\-\s]+$', new_name):
                QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                                   self.main_window.tr("项目名称只能包含字母、数字、下划线、横线和空格！"))
                return

        try:
            source_dir = os.path.join(self.get_current_project_group_dir(), project_name)
            target_dir = os.path.join(project_base, target_group, new_name)

            if os.path.exists(target_dir):
                QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                                   self.main_window.tr(f"目标位置已存在同名项目 '{new_name}'！"))
                return

            shutil.move(source_dir, target_dir)

            logger.info(f"项目剪切成功: {project_name} -> {target_group}/{new_name}")
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"项目 '{project_name}' 已剪切到 '{target_group}/{new_name}'！"))

            if self.main_window.current_project_name == project_name:
                self.main_window.current_project_name = None
                self.main_window.current_project_label.setText(self.main_window.tr("未选择项目"))
                self.main_window.project_path_label.setText("./Project/")
                self.main_window.settings.remove("current_project")

            self.refresh_project_list()

        except Exception as e:
            logger.error(f"剪切项目失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"剪切项目失败: {str(e)}"))