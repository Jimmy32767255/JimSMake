import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QProgressDialog, QMessageBox, QGroupBox,
    QCheckBox, QHeaderView, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


@dataclass
class ProjectInfo:
    """项目信息"""
    name: str
    path: str
    group: str
    config: Optional[Dict] = None
    is_valid: bool = False
    error_message: str = ""

    def load_config(self) -> bool:
        """加载项目配置"""
        config_path = os.path.join(self.path, "config.json")
        if not os.path.exists(config_path):
            self.error_message = "配置文件不存在"
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.is_valid = True
            return True
        except Exception as e:
            self.error_message = f"配置文件读取失败: {str(e)}"
            return False


@dataclass
class ProjectGroupInfo:
    """项目组信息"""
    name: str
    path: str
    projects: List[ProjectInfo] = field(default_factory=list)

    def load_projects(self) -> None:
        """加载项目组中的所有项目"""
        self.projects.clear()
        if not os.path.exists(self.path):
            return

        try:
            for item in os.listdir(self.path):
                item_path = os.path.join(self.path, item)
                if os.path.isdir(item_path):
                    project = ProjectInfo(name=item, path=item_path, group=self.name)
                    project.load_config()
                    self.projects.append(project)
        except Exception as e:
            logger.error(f"加载项目组 {self.name} 的项目失败: {e}")


class BatchGenerationWorker(QThread):
    """批量生成工作线程"""
    progress_updated = pyqtSignal(int)
    project_started = pyqtSignal(str)
    project_finished = pyqtSignal(str, bool, str)
    batch_finished = pyqtSignal(bool, str)

    def __init__(self, projects: List[ProjectInfo], project_manager, output_manager):
        super().__init__()
        self.projects = projects
        self.project_manager = project_manager
        self.output_manager = output_manager
        self.is_cancelled = False
        self.current_project_index = 0

    def cancel(self):
        """取消批量生成"""
        self.is_cancelled = True
        # 同时取消当前的生成任务
        if hasattr(self.output_manager.main_window, 'audio_processor') and \
           self.output_manager.main_window.audio_processor and \
           self.output_manager.main_window.audio_processor.isRunning():
            self.output_manager.main_window.audio_processor.cancel()

    def run(self):
        """执行批量生成"""
        total_projects = len(self.projects)
        success_count = 0
        failed_count = 0

        for i, project in enumerate(self.projects):
            if self.is_cancelled:
                self.batch_finished.emit(False, f"批量生成已取消。成功: {success_count}, 失败: {failed_count}")
                return

            self.current_project_index = i
            progress = int((i / total_projects) * 100)
            self.progress_updated.emit(progress)
            self.project_started.emit(f"[{project.group}] {project.name}")

            try:
                success, message = self._generate_project(project)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                self.project_finished.emit(f"[{project.group}] {project.name}", success, message)
            except Exception as e:
                failed_count += 1
                logger.error(f"生成项目 {project.name} 时出错: {e}")
                self.project_finished.emit(f"[{project.group}] {project.name}", False, str(e))

        final_progress = 100
        self.progress_updated.emit(final_progress)
        self.batch_finished.emit(
            failed_count == 0,
            f"批量生成完成。成功: {success_count}, 失败: {failed_count}"
        )

    def _generate_project(self, project: ProjectInfo) -> Tuple[bool, str]:
        """生成单个项目"""
        # 切换到项目
        self.project_manager.switch_project_group(project.group)
        self.project_manager.switch_project(project.name)

        # 检查项目配置
        if not project.is_valid:
            return False, project.error_message

        # 验证必要的配置
        config = project.config
        affirmation = config.get('affirmation', {})
        output = config.get('output', {})

        # 检查是否选择了生成选项
        if not output.get('generate_audio') and not output.get('generate_video'):
            return False, "未选择生成音频或视频"

        # 检查肯定语文件
        affirmation_file = affirmation.get('file', '')

        # 如果配置文件中没有肯定语文件，尝试按规范自动检测
        if not affirmation_file:
            affirmation_dir = os.path.join(project.path, "Assets", "Affirmation")
            # 首先查找 Raw.txt 对应的音频文件（如 zh_CN-huayan-medium.wav）
            raw_txt_path = os.path.join(affirmation_dir, "Raw.txt")
            if os.path.exists(raw_txt_path):
                # 查找 Affirmation 目录下的音频文件（排除 Raw.txt）
                affirmation_file = self._find_first_audio_file(affirmation_dir, exclude_names=["Raw.txt"])
            if not affirmation_file:
                return False, "生成音频需要选择肯定语音频文件"
            # 更新配置中的文件路径（使用相对路径）
            affirmation['file'] = os.path.relpath(affirmation_file, project.path)

        # 转换相对路径为绝对路径
        if affirmation_file and not os.path.isabs(affirmation_file):
            affirmation_file = os.path.join(project.path, affirmation_file)

        if affirmation_file and not os.path.exists(affirmation_file):
            return False, f"肯定语文件不存在: {affirmation_file}"

        # 保存当前配置
        self.project_manager.save_project_config(project.path)

        # 执行生成（这里使用同步方式等待生成完成）
        try:
            # 使用 output_manager 的生成逻辑，但需要等待完成
            result = self._execute_generation(project)
            return result
        except Exception as e:
            logger.error(f"生成项目 {project.name} 失败: {e}")
            return False, str(e)

    def _execute_generation(self, project: ProjectInfo) -> Tuple[bool, str]:
        """执行生成操作"""
        import tempfile
        from datetime import datetime
        from Processors.AudioProcessor import AudioProcessor

        config = project.config
        affirmation = config.get('affirmation', {})
        background = config.get('background', {})
        overlay = config.get('overlay', {})
        freq_track = config.get('freq_track', {})
        output = config.get('output', {})
        metadata = config.get('metadata', {})

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generate_audio = output.get('generate_audio', True)
        generate_video = output.get('generate_video', False)

        affirmation_file = affirmation.get('file', '')
        if affirmation_file and not os.path.isabs(affirmation_file):
            affirmation_file = os.path.join(project.path, affirmation_file)

        audio_format = output.get('audio_format', 'WAV')
        format_ext = audio_format.lower()

        if generate_video and not generate_audio:
            temp_dir = tempfile.gettempdir()
            audio_output_path = os.path.join(temp_dir, f"SMake_temp_audio_{timestamp}.wav")
        else:
            audio_output_path = os.path.join(
                project.path, "Releases", "Audio", f"{timestamp}.{format_ext}"
            )

        output_dir = os.path.dirname(audio_output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 检查背景音文件，如果没有则尝试按规范自动检测
        background_file = background.get('file', '')
        if not background_file:
            assets_dir = os.path.join(project.path, "Assets")
            # 首先查找 BGM.wav
            bgm_path = os.path.join(assets_dir, "BGM.wav")
            if os.path.exists(bgm_path):
                background_file = bgm_path
                background['file'] = "Assets/BGM.wav"
            else:
                # 如果没有 BGM.wav，查找其他音频文件（排除 Raw.txt）
                background_file = self._find_first_audio_file(assets_dir, exclude_names=["Raw.txt"])
                if background_file:
                    background['file'] = os.path.relpath(background_file, project.path)

        if background_file and not os.path.isabs(background_file):
            background_file = os.path.join(project.path, background_file)

        # 检查视频图片，如果没有则尝试按规范自动检测
        video_image = output.get('video_image', '')
        if not video_image:
            assets_dir = os.path.join(project.path, "Assets")
            # 首先查找 Visualization.png
            viz_path = os.path.join(assets_dir, "Visualization.png")
            if os.path.exists(viz_path):
                video_image = viz_path
                output['video_image'] = "Assets/Visualization.png"
            else:
                # 如果没有 Visualization.png，查找其他图片文件
                video_image = self._find_first_image_file(assets_dir)
                if video_image:
                    output['video_image'] = os.path.relpath(video_image, project.path)

        if video_image and not os.path.isabs(video_image):
            video_image = os.path.join(project.path, video_image)

        params = {
            'affirmation_file': affirmation_file,
            'background_file': background_file,
            'volume': affirmation.get('volume', -23.0),
            'frequency_mode': ['Raw（保持不变）', 'UG（亚超声波）', '传统（次声波）'].index(
                affirmation.get('frequency_mode', 'Raw（保持不变）')
            ) if affirmation.get('frequency_mode') else 0,
            'speed': affirmation.get('speed', 1.0),
            'reverse': affirmation.get('reverse', False),
            'overlay_times': overlay.get('times', 1),
            'overlay_interval': overlay.get('interval', 1.0),
            'volume_decrease': overlay.get('volume_decrease', 0.0),
            'background_volume': background.get('volume', 0.0),
            'freq_track_enabled': freq_track.get('enabled', False),
            'freq_track_freq': freq_track.get('frequency', '432'),
            'freq_track_volume': freq_track.get('volume', -23.0),
            'output_format': audio_format,
            'output_path': audio_output_path,
            'generate_audio': generate_audio,
            'generate_video': generate_video,
            'video_image': video_image,
            'video_format': output.get('video_format', 'MP4'),
            'video_resolution': output.get('video_resolution', '1920x1080'),
            'metadata_title': metadata.get('title', ''),
            'metadata_author': metadata.get('author', ''),
            'ensure_integrity': config.get('ensure_integrity', False)
        }

        # 创建处理器并执行
        processor = AudioProcessor(params)

        # 使用事件循环等待处理完成
        from PyQt5.QtCore import QEventLoop
        loop = QEventLoop()
        result = {'success': False, 'message': ''}

        def on_finished(output_path):
            result['success'] = True
            result['message'] = f"音频生成成功: {output_path}"
            loop.quit()

        def on_error(error_msg):
            result['success'] = False
            result['message'] = error_msg
            loop.quit()

        processor.processing_finished.connect(on_finished)
        processor.processing_error.connect(on_error)
        processor.start()

        # 等待处理完成，但定期检查是否被取消
        while processor.isRunning():
            if self.is_cancelled:
                processor.cancel()
                processor.wait()
                return False, "生成已取消"
            self.msleep(100)

        loop.exec_()

        # 如果需要生成视频
        if result['success'] and generate_video:
            video_result = self._generate_video(project, audio_output_path, timestamp)
            if not video_result[0]:
                return video_result

        return result['success'], result['message']

    def _generate_video(self, project: ProjectInfo, audio_path: str, timestamp: str) -> Tuple[bool, str]:
        """生成视频"""
        from datetime import datetime
        from Processors.VideoProcessor import VideoProcessor

        config = project.config
        output = config.get('output', {})
        metadata = config.get('metadata', {})

        video_format = output.get('video_format', 'MP4')
        format_ext = {
            'MP4': '.mp4',
            'AVI': '.avi',
            'MKV': '.mkv'
        }.get(video_format, '.mp4')

        video_output_path = os.path.join(
            project.path, "Releases", "Video", f"{timestamp}{format_ext}"
        )

        video_output_dir = os.path.dirname(video_output_path)
        if video_output_dir and not os.path.exists(video_output_dir):
            os.makedirs(video_output_dir, exist_ok=True)

        video_image = output.get('video_image', '')
        if video_image and not os.path.isabs(video_image):
            video_image = os.path.join(project.path, video_image)

        video_params = {
            'audio_path': audio_path,
            'video_image': video_image,
            'video_output_path': video_output_path,
            'video_format': video_format,
            'video_resolution': output.get('video_resolution', '1920x1080'),
            'metadata_title': metadata.get('title', ''),
            'metadata_author': metadata.get('author', '')
        }

        processor = VideoProcessor(video_params)

        from PyQt5.QtCore import QEventLoop
        loop = QEventLoop()
        result = {'success': False, 'message': ''}

        def on_finished(output_path):
            result['success'] = True
            result['message'] = f"视频生成成功: {output_path}"
            loop.quit()

        def on_error(error_msg):
            result['success'] = False
            result['message'] = error_msg
            loop.quit()

        processor.processing_finished.connect(on_finished)
        processor.processing_error.connect(on_error)
        processor.start()

        while processor.isRunning():
            if self.is_cancelled:
                processor.cancel()
                processor.wait()
                return False, "视频生成已取消"
            self.msleep(100)

        loop.exec_()

        return result['success'], result['message']

    def _find_first_audio_file(self, directory: str, exclude_names: List[str] = None) -> Optional[str]:
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

    def _find_first_image_file(self, directory: str) -> Optional[str]:
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


class BatchProcessorDialog(QDialog):
    """批量处理对话框"""

    def __init__(self, parent, project_manager, output_manager):
        super().__init__(parent)
        self.project_manager = project_manager
        self.output_manager = output_manager
        self.selected_projects: List[ProjectInfo] = []
        self.project_groups: List[ProjectGroupInfo] = []
        self.batch_worker: Optional[BatchGenerationWorker] = None

        self.setWindowTitle(self.tr("批量生成项目"))
        self.setMinimumSize(700, 500)
        self.init_ui()
        self.load_project_structure()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 说明标签
        info_label = QLabel(self.tr("请选择要批量生成的项目。系统将按项目配置依次生成。"))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 项目树形视图
        tree_group = QGroupBox(self.tr("项目选择"))
        tree_layout = QVBoxLayout()

        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels([self.tr("名称"), self.tr("状态"), self.tr("路径")])
        self.project_tree.setColumnWidth(0, 200)
        self.project_tree.setColumnWidth(1, 100)
        self.project_tree.setColumnWidth(2, 300)
        self.project_tree.header().setStretchLastSection(True)
        self.project_tree.setSelectionMode(QTreeWidget.NoSelection)
        self.project_tree.itemChanged.connect(self.on_item_changed)

        tree_layout.addWidget(self.project_tree)

        # 全选/取消全选按钮
        select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton(self.tr("全选"))
        self.select_all_btn.clicked.connect(self.select_all)
        select_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton(self.tr("取消全选"))
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        select_layout.addWidget(self.deselect_all_btn)

        self.select_valid_btn = QPushButton(self.tr("仅选有效项目"))
        self.select_valid_btn.clicked.connect(self.select_valid_only)
        select_layout.addWidget(self.select_valid_btn)

        select_layout.addStretch()
        tree_layout.addLayout(select_layout)

        tree_group.setLayout(tree_layout)
        layout.addWidget(tree_group)

        # 统计信息
        self.stats_label = QLabel(self.tr("已选择: 0 个项目"))
        layout.addWidget(self.stats_label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton(self.tr("取消"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.generate_btn = QPushButton(self.tr("开始批量生成"))
        self.generate_btn.setStyleSheet("font-weight: bold;")
        self.generate_btn.clicked.connect(self.start_batch_generation)
        button_layout.addWidget(self.generate_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_project_structure(self):
        """加载项目结构"""
        self.project_tree.clear()
        self.project_groups.clear()

        project_base = self.project_manager.get_project_base_dir()
        if not os.path.exists(project_base):
            return

        try:
            for item in os.listdir(project_base):
                item_path = os.path.join(project_base, item)
                if os.path.isdir(item_path):
                    group = ProjectGroupInfo(name=item, path=item_path)
                    group.load_projects()
                    self.project_groups.append(group)

                    # 创建项目组节点
                    group_item = QTreeWidgetItem(self.project_tree)
                    group_item.setText(0, item)
                    group_item.setText(1, self.tr("项目组"))
                    group_item.setText(2, item_path)
                    group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable)
                    group_item.setCheckState(0, Qt.Unchecked)
                    group_item.setData(0, Qt.UserRole, ('group', group))

                    # 添加项目节点
                    for project in group.projects:
                        project_item = QTreeWidgetItem(group_item)
                        project_item.setText(0, project.name)
                        project_item.setText(2, project.path)
                        project_item.setFlags(project_item.flags() | Qt.ItemIsUserCheckable)
                        project_item.setCheckState(0, Qt.Unchecked)
                        project_item.setData(0, Qt.UserRole, ('project', project))

                        if project.is_valid:
                            project_item.setText(1, self.tr("有效"))
                            project_item.setForeground(1, Qt.darkGreen)
                        else:
                            project_item.setText(1, self.tr("无效"))
                            project_item.setToolTip(1, project.error_message)
                            project_item.setForeground(1, Qt.red)

                    group_item.setExpanded(True)

        except Exception as e:
            logger.error(f"加载项目结构失败: {e}")
            QMessageBox.critical(self, self.tr("错误"), self.tr(f"加载项目结构失败: {str(e)}"))

        self.update_stats()

    def select_all(self):
        """全选"""
        self._set_all_check_state(Qt.Checked)

    def deselect_all(self):
        """取消全选"""
        self._set_all_check_state(Qt.Unchecked)

    def select_valid_only(self):
        """仅选择有效项目"""
        root = self.project_tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            for j in range(group_item.childCount()):
                project_item = group_item.child(j)
                item_type, data = project_item.data(0, Qt.UserRole)
                if item_type == 'project':
                    project: ProjectInfo = data
                    if project.is_valid:
                        project_item.setCheckState(0, Qt.Checked)
                    else:
                        project_item.setCheckState(0, Qt.Unchecked)
            # 更新项目组复选框状态
            self._update_group_check_state(group_item)
        self.update_stats()

    def _set_all_check_state(self, state: Qt.CheckState):
        """设置所有项目的选中状态"""
        root = self.project_tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            group_item.setCheckState(0, state)
            for j in range(group_item.childCount()):
                project_item = group_item.child(j)
                project_item.setCheckState(0, state)
        self.update_stats()

    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        """处理树形项目复选框状态变化"""
        if column != 0:
            return

        # 获取项目数据
        item_data = item.data(0, Qt.UserRole)
        if item_data is None:
            return

        # 暂时断开信号，避免递归
        self.project_tree.itemChanged.disconnect(self.on_item_changed)

        try:
            item_type, data = item_data

            if item_type == 'group':
                # 项目组状态改变，同步所有子项目
                state = item.checkState(0)
                for j in range(item.childCount()):
                    project_item = item.child(j)
                    project_item.setCheckState(0, state)
            elif item_type == 'project':
                # 项目状态改变，更新项目组状态
                parent = item.parent()
                if parent:
                    self._update_group_check_state(parent)

            self.update_stats()
        finally:
            # 重新连接信号
            self.project_tree.itemChanged.connect(self.on_item_changed)

    def _update_group_check_state(self, group_item: QTreeWidgetItem):
        """根据子项目更新项目组的复选框状态"""
        checked_count = 0
        total_count = group_item.childCount()

        for j in range(total_count):
            project_item = group_item.child(j)
            if project_item.checkState(0) == Qt.Checked:
                checked_count += 1

        if checked_count == 0:
            group_item.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count:
            group_item.setCheckState(0, Qt.Checked)
        else:
            group_item.setCheckState(0, Qt.PartiallyChecked)

    def update_stats(self):
        """更新统计信息"""
        selected_count = 0
        valid_count = 0
        invalid_count = 0

        root = self.project_tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            for j in range(group_item.childCount()):
                project_item = group_item.child(j)
                if project_item.checkState(0) == Qt.Checked:
                    selected_count += 1
                    item_type, data = project_item.data(0, Qt.UserRole)
                    if item_type == 'project':
                        project: ProjectInfo = data
                        if project.is_valid:
                            valid_count += 1
                        else:
                            invalid_count += 1

        self.stats_label.setText(
            self.tr(f"已选择: {selected_count} 个项目 (有效: {valid_count}, 无效: {invalid_count})")
        )

        # 启用/禁用生成按钮
        self.generate_btn.setEnabled(valid_count > 0)

    def get_selected_projects(self) -> List[ProjectInfo]:
        """获取选中的项目列表"""
        selected = []
        root = self.project_tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            for j in range(group_item.childCount()):
                project_item = group_item.child(j)
                if project_item.checkState(0) == Qt.Checked:
                    item_type, data = project_item.data(0, Qt.UserRole)
                    if item_type == 'project':
                        project: ProjectInfo = data
                        if project.is_valid:
                            selected.append(project)
        return selected

    def start_batch_generation(self):
        """开始批量生成"""
        selected_projects = self.get_selected_projects()
        if not selected_projects:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请至少选择一个有效的项目！"))
            return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            self.tr("确认批量生成"),
            self.tr(f"确定要批量生成 {len(selected_projects)} 个项目吗？\n\n"
                   "注意：此操作将依次加载每个项目的配置并执行生成，可能需要较长时间。"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 禁用UI
        self.set_ui_enabled(False)

        # 创建进度对话框
        self.progress_dialog = QProgressDialog(
            self.tr("准备批量生成..."),
            self.tr("取消"),
            0, 100,
            self
        )
        self.progress_dialog.setWindowTitle(self.tr("批量生成进度"))
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self.cancel_batch_generation)

        # 创建工作线程
        self.batch_worker = BatchGenerationWorker(
            selected_projects,
            self.project_manager,
            self.output_manager
        )

        self.batch_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.batch_worker.project_started.connect(
            lambda name: self.progress_dialog.setLabelText(self.tr(f"正在生成: {name}"))
        )
        self.batch_worker.project_finished.connect(self.on_project_finished)
        self.batch_worker.batch_finished.connect(self.on_batch_finished)

        self.progress_dialog.show()
        self.batch_worker.start()

    def on_project_finished(self, project_name: str, success: bool, message: str):
        """单个项目生成完成回调"""
        status = self.tr("成功") if success else self.tr("失败")
        logger.info(f"批量生成 - {project_name}: {status} - {message}")

    def on_batch_finished(self, success: bool, message: str):
        """批量生成完成回调"""
        self.progress_dialog.close()
        self.set_ui_enabled(True)

        if success:
            QMessageBox.information(self, self.tr("批量生成完成"), message)
        else:
            QMessageBox.warning(self, self.tr("批量生成结果"), message)

        self.batch_worker = None

    def cancel_batch_generation(self):
        """取消批量生成"""
        if self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.cancel()
            self.batch_worker.wait()

    def set_ui_enabled(self, enabled: bool):
        """设置UI启用状态"""
        self.project_tree.setEnabled(enabled)
        self.select_all_btn.setEnabled(enabled)
        self.deselect_all_btn.setEnabled(enabled)
        self.select_valid_btn.setEnabled(enabled)
        self.generate_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)

    def changeEvent(self, event):
        """处理语言变更事件"""
        if event.type() == event.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def retranslate_ui(self):
        """重新翻译UI"""
        self.setWindowTitle(self.tr("批量生成项目"))
        # 其他控件的翻译会在下次打开时生效
