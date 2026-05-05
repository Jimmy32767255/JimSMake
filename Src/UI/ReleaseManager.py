import os
import subprocess
import platform
from loguru import logger
from PyQt5.QtWidgets import (
    QMessageBox, QInputDialog, QListWidgetItem,
    QMenu, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


class ReleaseManager:
    """输出文件管理器 - 管理项目的输出文件（音频/视频）"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.output_list = None

    def setup_ui(self, output_list_widget):
        """设置UI组件"""
        self.output_list = output_list_widget
        self.output_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output_list.customContextMenuRequested.connect(self.show_context_menu)
        self.output_list.itemDoubleClicked.connect(self.open_with_system_player)

    def refresh_output_list(self):
        """刷新输出文件列表"""
        if self.output_list is None:
            logger.warning("output_list 未设置")
            return

        self.output_list.clear()
        project_dir = self.main_window.get_current_project_dir()
        logger.debug(f"刷新输出列表，项目目录: {project_dir}")

        if not project_dir:
            logger.warning("项目目录为空")
            # 显示提示信息
            item = QListWidgetItem(self.main_window.tr("请先选择一个项目"))
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.output_list.addItem(item)
            return

        if not os.path.exists(project_dir):
            logger.warning(f"项目目录不存在: {project_dir}")
            # 显示提示信息
            item = QListWidgetItem(self.main_window.tr("项目目录不存在"))
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.output_list.addItem(item)
            return

        # 扫描音频和视频输出目录
        releases_dir = os.path.join(project_dir, "Releases")
        audio_dir = os.path.join(releases_dir, "Audio")
        video_dir = os.path.join(releases_dir, "Video")

        output_files = []

        # 扫描音频文件
        if os.path.exists(audio_dir):
            logger.debug(f"扫描音频目录: {audio_dir}")
            for file in os.listdir(audio_dir):
                file_path = os.path.join(audio_dir, file)
                if os.path.isfile(file_path):
                    output_files.append((file, file_path, "audio"))
                    logger.debug(f"找到音频文件: {file}")
        else:
            logger.debug(f"音频目录不存在: {audio_dir}")

        # 扫描视频文件
        if os.path.exists(video_dir):
            logger.debug(f"扫描视频目录: {video_dir}")
            for file in os.listdir(video_dir):
                file_path = os.path.join(video_dir, file)
                if os.path.isfile(file_path):
                    output_files.append((file, file_path, "video"))
                    logger.debug(f"找到视频文件: {file}")
        else:
            logger.debug(f"视频目录不存在: {video_dir}")

        # 按修改时间排序（最新的在前）
        output_files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)

        # 添加到列表
        for file_name, file_path, file_type in output_files:
            item = QListWidgetItem(file_name)
            item.setData(Qt.UserRole, file_path)
            item.setData(Qt.UserRole + 1, file_type)

            # 设置图标
            if file_type == "audio":
                item.setIcon(self._get_audio_icon())
            else:
                item.setIcon(self._get_video_icon())

            # 添加文件大小信息
            size = os.path.getsize(file_path)
            size_str = self._format_file_size(size)
            item.setToolTip(f"{file_path}\n{self.main_window.tr('大小')}: {size_str}")

            self.output_list.addItem(item)

        if len(output_files) == 0:
            # 显示提示信息
            item = QListWidgetItem(self.main_window.tr("暂无输出文件"))
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.output_list.addItem(item)

        logger.debug(f"刷新输出列表，找到 {len(output_files)} 个文件")

    def _get_audio_icon(self):
        """获取音频文件图标"""
        return QIcon.fromTheme("audio-x-generic")

    def _get_video_icon(self):
        """获取视频文件图标"""
        return QIcon.fromTheme("video-x-generic")

    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.output_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self.output_list)

        # 打开方式
        open_action = menu.addAction(self.main_window.tr("用系统播放器打开"))
        open_action.triggered.connect(lambda: self.open_with_system_player(item))

        open_folder_action = menu.addAction(self.main_window.tr("在文件资源管理器中打开"))
        open_folder_action.triggered.connect(lambda: self.open_in_explorer(item))

        menu.addSeparator()

        # 重命名
        rename_action = menu.addAction(self.main_window.tr("重命名"))
        rename_action.triggered.connect(lambda: self.rename_output_file(item))

        menu.addSeparator()

        # 删除
        delete_action = menu.addAction(self.main_window.tr("删除"))
        delete_action.triggered.connect(lambda: self.delete_output_file(item))

        menu.exec_(self.output_list.viewport().mapToGlobal(position))

    def get_selected_file_path(self, item=None):
        """获取选中文件的路径"""
        if item is None:
            item = self.output_list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None

    def open_with_system_player(self, item=None):
        """用系统播放器打开文件"""
        file_path = self.get_selected_file_path(item)
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("文件不存在！"))
            return

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", file_path], check=True)
            logger.info(f"用系统播放器打开: {file_path}")
        except Exception as e:
            logger.error(f"打开文件失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"打开文件失败: {str(e)}"))

    def open_in_explorer(self, item=None):
        """在文件资源管理器中打开"""
        file_path = self.get_selected_file_path(item)
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("文件不存在！"))
            return

        try:
            folder_path = os.path.dirname(file_path)
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", "/select,", file_path], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", folder_path], check=True)
            logger.info(f"在文件资源管理器中打开: {folder_path}")
        except Exception as e:
            logger.error(f"打开文件夹失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"打开文件夹失败: {str(e)}"))

    def rename_output_file(self, item=None):
        """重命名输出文件"""
        file_path = self.get_selected_file_path(item)
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("文件不存在！"))
            return

        old_name = os.path.basename(file_path)
        old_ext = os.path.splitext(old_name)[1]

        new_name, ok = QInputDialog.getText(
            self.main_window,
            self.main_window.tr("重命名文件"),
            self.main_window.tr("请输入新文件名（不含扩展名）："),
            text=os.path.splitext(old_name)[0]
        )

        if not ok or not new_name:
            return

        # 添加原扩展名
        new_name_with_ext = new_name + old_ext
        new_path = os.path.join(os.path.dirname(file_path), new_name_with_ext)

        # 检查新文件名是否已存在
        if os.path.exists(new_path):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("该文件名已存在！"))
            return

        try:
            os.rename(file_path, new_path)
            logger.info(f"重命名文件: {file_path} -> {new_path}")

            # 更新列表项
            if item:
                item.setText(new_name_with_ext)
                item.setData(Qt.UserRole, new_path)
                item.setToolTip(f"{new_path}\n{self.main_window.tr('大小')}: {self._format_file_size(os.path.getsize(new_path))}")

            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"文件重命名成功！\n新名称: {new_name_with_ext}"))
        except Exception as e:
            logger.error(f"重命名文件失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"重命名失败: {str(e)}"))

    def delete_output_file(self, item=None):
        """删除输出文件"""
        file_path = self.get_selected_file_path(item)
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("文件不存在！"))
            return

        file_name = os.path.basename(file_path)

        reply = QMessageBox.question(
            self.main_window,
            self.main_window.tr("确认删除"),
            self.main_window.tr(f"确定要删除文件 '{file_name}' 吗？\n此操作不可撤销！"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            os.remove(file_path)
            logger.info(f"删除文件: {file_path}")

            # 从列表中移除
            if item:
                self.output_list.takeItem(self.output_list.row(item))

            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr("文件删除成功！"))
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"删除失败: {str(e)}"))

    def delete_all_outputs(self):
        """删除所有输出文件"""
        project_dir = self.main_window.get_current_project_dir()
        if not project_dir or not os.path.exists(project_dir):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("请先选择一个项目！"))
            return

        releases_dir = os.path.join(project_dir, "Releases")
        if not os.path.exists(releases_dir):
            QMessageBox.information(self.main_window, self.main_window.tr("提示"),
                                   self.main_window.tr("没有可删除的输出文件。"))
            return

        # 统计文件数量
        audio_dir = os.path.join(releases_dir, "Audio")
        video_dir = os.path.join(releases_dir, "Video")

        file_count = 0
        if os.path.exists(audio_dir):
            file_count += len([f for f in os.listdir(audio_dir) if os.path.isfile(os.path.join(audio_dir, f))])
        if os.path.exists(video_dir):
            file_count += len([f for f in os.listdir(video_dir) if os.path.isfile(os.path.join(video_dir, f))])

        if file_count == 0:
            QMessageBox.information(self.main_window, self.main_window.tr("提示"),
                                   self.main_window.tr("没有可删除的输出文件。"))
            return

        reply = QMessageBox.question(
            self.main_window,
            self.main_window.tr("确认删除所有"),
            self.main_window.tr(f"确定要删除所有输出文件吗？\n共 {file_count} 个文件，此操作不可撤销！"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            deleted_count = 0
            # 删除音频文件
            if os.path.exists(audio_dir):
                for file in os.listdir(audio_dir):
                    file_path = os.path.join(audio_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1

            # 删除视频文件
            if os.path.exists(video_dir):
                for file in os.listdir(video_dir):
                    file_path = os.path.join(video_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1

            logger.info(f"删除所有输出文件，共 {deleted_count} 个")

            # 刷新列表（仅在output_list已设置时）
            if self.output_list is not None:
                self.refresh_output_list()

            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"成功删除 {deleted_count} 个文件！"))
        except Exception as e:
            logger.error(f"删除所有文件失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"删除失败: {str(e)}"))

    def export_output_file(self, item=None):
        """导出输出文件到指定位置"""
        file_path = self.get_selected_file_path(item)
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("文件不存在！"))
            return

        file_name = os.path.basename(file_path)

        save_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            self.main_window.tr("导出文件"),
            file_name,
            self.main_window.tr("所有文件 (*)")
        )

        if not save_path:
            return

        try:
            import shutil
            shutil.copy2(file_path, save_path)
            logger.info(f"导出文件: {file_path} -> {save_path}")
            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"文件导出成功！\n保存位置: {save_path}"))
        except Exception as e:
            logger.error(f"导出文件失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"导出失败: {str(e)}"))
