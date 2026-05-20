"""
更新检查器模块
用于检查软件更新
"""

import json
import urllib.request
import urllib.error
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from loguru import logger


class UpdateCheckerThread(QThread):
    """在后台线程中检查更新的线程"""

    # 信号：检查完成 (是否有更新, 最新版本, 下载链接, 更新说明)
    check_finished = pyqtSignal(bool, str, str, str)
    # 信号：检查出错 (错误信息)
    check_error = pyqtSignal(str)

    # GitHub API 地址
    GITHUB_API_URL = "https://api.github.com/repos/Jimmy32767255/JimSMake/releases/latest"
    # GitHub Releases 页面
    GITHUB_RELEASES_URL = "https://github.com/Jimmy32767255/JimSMake/releases/latest"

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        """执行更新检查"""
        try:
            logger.info(f"开始检查更新，当前版本: {self.current_version}")

            # 设置请求头
            headers = {
                'User-Agent': 'JimSMake-UpdateChecker',
                'Accept': 'application/vnd.github.v3+json'
            }

            # 创建请求
            request = urllib.request.Request(
                self.GITHUB_API_URL,
                headers=headers
            )

            # 发送请求（timeout参数在urlopen中）
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            # 解析最新版本信息
            latest_version = data.get('tag_name', '')
            body = data.get('body', '无更新说明')

            # 比较版本号
            has_update = self._compare_versions(self.current_version, latest_version)

            logger.info(f"最新版本: {latest_version}, 是否有更新: {has_update}")

            self.check_finished.emit(has_update, latest_version, self.GITHUB_RELEASES_URL, body)

        except urllib.error.URLError as e:
            error_msg = f"网络错误: {str(e)}"
            logger.error(f"检查更新失败: {error_msg}")
            self.check_error.emit(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"解析响应失败: {str(e)}"
            logger.error(f"检查更新失败: {error_msg}")
            self.check_error.emit(error_msg)
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(f"检查更新失败: {error_msg}")
            self.check_error.emit(error_msg)

    def _parse_version(self, version_str):
        """
        解析版本号字符串，只提取数字部分
        返回: 主版本号列表
        例如: "V2.0.1R" -> [2, 0, 1]
               "2.1.0a3" -> [2, 1, 0]
               "3.0.0-Luna" -> [3, 0, 0]
        """
        import re

        # 移除前缀 V/v
        version = version_str.lower().strip()
        if version.startswith('v'):
            version = version[1:]

        # 只提取数字部分，移除数字后的所有非数字内容
        # 匹配模式: 数字.数字.数字...
        match = re.match(r'^(\d+(?:\.\d+)*)', version)
        if not match:
            logger.warning(f"无法解析版本号: {version_str}")
            return [0]

        # 解析主版本号
        main_version_str = match.group(1)
        main_version = [int(x) for x in main_version_str.split('.')]

        return main_version

    def _compare_versions(self, current, latest):
        """
        比较版本号
        返回 True 如果有新版本可用
        支持格式: V2.0.1, 2.0.1R, 2.1.0a, 2.1.0-Luna, 3.0.0_CodeName 等
        只比较数字部分，忽略数字后的所有内容
        """
        try:
            current_version = self._parse_version(current)
            latest_version = self._parse_version(latest)

            logger.debug(f"版本比较 - 当前: {current} -> {current_version}, 最新: {latest} -> {latest_version}")

            # 比较版本号
            for i in range(max(len(current_version), len(latest_version))):
                curr = current_version[i] if i < len(current_version) else 0
                late = latest_version[i] if i < len(latest_version) else 0

                if late > curr:
                    return True
                elif late < curr:
                    return False

            return False  # 版本相同
        except Exception as e:
            logger.error(f"版本比较失败: {e}")
            return False


class UpdateChecker:
    """更新检查器"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.check_thread = None

    def check_for_updates(self, silent=False):
        """
        检查更新
        :param silent: 如果为True，在没有更新时不显示提示
        """
        from Main import APP_VERSION

        logger.info(f"启动更新检查 (静默模式: {silent})")

        # 创建并启动检查线程
        self.check_thread = UpdateCheckerThread(APP_VERSION)
        self.check_thread.check_finished.connect(
            lambda has_update, latest, url, body: self._on_check_finished(has_update, latest, url, body, silent)
        )
        self.check_thread.check_error.connect(
            lambda error: self._on_check_error(error, silent)
        )
        self.check_thread.start()

    def _on_check_finished(self, has_update, latest_version, download_url, release_notes, silent):
        """检查完成的回调"""
        from Main import APP_VERSION

        if has_update:
            # 有新版本
            msg_box = QMessageBox(self.main_window)
            msg_box.setWindowTitle(self.main_window.tr("发现新版本"))
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setText(
                f"<b>{self.main_window.tr('发现新版本！')}</b><br><br>"
                f"{self.main_window.tr('当前版本:')} {APP_VERSION}<br>"
                f"{self.main_window.tr('最新版本:')} {latest_version}<br><br>"
                f"{self.main_window.tr('是否前往下载页面？')}"
            )
            msg_box.setInformativeText(
                f"<b>{self.main_window.tr('更新说明:')}</b><br>"
                f"<pre style='white-space: pre-wrap; word-wrap: break-word;'>{release_notes}</pre>"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            msg_box.button(QMessageBox.Yes).setText(self.main_window.tr("前往下载"))
            msg_box.button(QMessageBox.No).setText(self.main_window.tr("稍后提醒"))

            reply = msg_box.exec_()

            if reply == QMessageBox.Yes:
                import webbrowser
                webbrowser.open(download_url)
                logger.info(f"用户选择前往下载页面: {download_url}")
        else:
            # 没有更新
            if not silent:
                QMessageBox.information(
                    self.main_window,
                    self.main_window.tr("已是最新版本"),
                    f"{self.main_window.tr('当前版本')} {APP_VERSION} {self.main_window.tr('已是最新版本。')}"
                )
            logger.info("当前已是最新版本")

    def _on_check_error(self, error_msg, silent):
        """检查出错的回调"""
        logger.error(f"更新检查失败: {error_msg}")
        if not silent:
            QMessageBox.warning(
                self.main_window,
                self.main_window.tr("检查更新失败"),
                f"{self.main_window.tr('无法检查更新:')}\n{error_msg}\n\n"
                f"{self.main_window.tr('请检查网络连接或稍后重试。')}"
            )


# 导入 Qt
from PyQt5.QtCore import Qt
