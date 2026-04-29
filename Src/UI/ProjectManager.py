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
            if hasattr(self.main_window, 'metadata_title') and self.main_window.metadata_title is not None:
                self.main_window.metadata_title.clear()
            if hasattr(self.main_window, 'metadata_author') and self.main_window.metadata_author is not None:
                self.main_window.metadata_author.clear()
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            metadata = config.get('metadata', {})
            if hasattr(self.main_window, 'metadata_title') and self.main_window.metadata_title is not None:
                self.main_window.metadata_title.setText(metadata.get('title', ''))
            if hasattr(self.main_window, 'metadata_author') and self.main_window.metadata_author is not None:
                self.main_window.metadata_author.setText(metadata.get('author', ''))

            logger.info(f"项目配置加载成功: {config_path}")
            logger.debug(f"配置内容: {config}")

        except json.JSONDecodeError as e:
            logger.error(f"项目配置文件格式错误: {config_path}, 错误: {e}")
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr(f"项目配置文件格式错误，将使用默认配置。"))
        except Exception as e:
            logger.error(f"加载项目配置失败: {config_path}, 错误: {e}")

    def save_project_config(self, project_dir):
        """保存项目配置文件"""
        config_path = os.path.join(project_dir, "config.json")
        logger.debug(f"保存项目配置: {config_path}")

        try:
            config = {
                "version": "1.0",
                "metadata": {
                    "title": self.main_window.metadata_title.text() if hasattr(self.main_window, 'metadata_title') else "",
                    "author": self.main_window.metadata_author.text() if hasattr(self.main_window, 'metadata_author') else ""
                }
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info(f"项目配置保存成功: {config_path}")

        except Exception as e:
            logger.error(f"保存项目配置失败: {config_path}, 错误: {e}")

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