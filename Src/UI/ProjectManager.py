import os
import json
import sys
from loguru import logger
from PyQt5.QtWidgets import QMessageBox


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
            self._set_default_config()
        except Exception as e:
            logger.error(f"加载项目配置失败: {config_path}, 错误: {e}")
            self._set_default_config()

    def _set_default_config(self):
        """设置默认配置"""
        if hasattr(self.main_window, 'metadata_title') and self.main_window.metadata_title is not None:
            self.main_window.metadata_title.clear()
        if hasattr(self.main_window, 'metadata_author') and self.main_window.metadata_author is not None:
            self.main_window.metadata_author.clear()

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
        """将目录压缩为ZIP文件"""
        import zipfile

        logger.debug(f"开始压缩为ZIP: {source_dir} -> {output_path}")

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    logger.debug(f"添加文件到ZIP: {arcname}")

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
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as zf:
                    file_list = zf.namelist()
            elif file_path.endswith('.tar.xz'):
                import tarfile
                with tarfile.open(file_path, 'r:xz') as tf:
                    file_list = [m.name for m in tf.getmembers()]
            else:
                return "unknown"

            top_dirs = set()
            for name in file_list:
                parts = name.split('/')
                if len(parts) > 0 and parts[0]:
                    top_dirs.add(parts[0])

            if len(top_dirs) == 1:
                top_dir = list(top_dirs)[0]
                has_config = any('config.json' in f for f in file_list)
                has_assets = any('Assets/' in f for f in file_list)
                has_readme = any('README.md' in f for f in file_list)

                if has_config and has_assets:
                    return "project"

                subdirs = set()
                for name in file_list:
                    parts = name.split('/')
                    if len(parts) > 1 and parts[1]:
                        subdirs.add(parts[1])

                if len(subdirs) > 0:
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
                reply = QMessageBox.question(
                    self.main_window,
                    self.main_window.tr("选择导入类型"),
                    self.main_window.tr("无法自动检测导入类型。请选择要导入为项目还是项目组？"),
                    self.main_window.tr("项目"),
                    self.main_window.tr("项目组")
                )
                if reply == 0:
                    self._import_project(file_path)
                else:
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

        target_dir = self.get_current_project_group_dir()

        if file_path.endswith('.zip'):
            self._extract_zip(file_path, target_dir)
        elif file_path.endswith('.tar.xz'):
            self._extract_tar_xz(file_path, target_dir)

        logger.info(f"项目导入成功到: {target_dir}")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                               self.main_window.tr("项目导入成功！"))

        self.refresh_project_list()

    def _import_project_group(self, file_path):
        """导入项目组"""
        logger.info(f"开始导入项目组: {file_path}")

        target_dir = self.get_project_base_dir()

        if file_path.endswith('.zip'):
            self._extract_zip(file_path, target_dir)
        elif file_path.endswith('.tar.xz'):
            self._extract_tar_xz(file_path, target_dir)

        logger.info(f"项目组导入成功到: {target_dir}")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                               self.main_window.tr("项目组导入成功！"))

        self.refresh_project_group_list()

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