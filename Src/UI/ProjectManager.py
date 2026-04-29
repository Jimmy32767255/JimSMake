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