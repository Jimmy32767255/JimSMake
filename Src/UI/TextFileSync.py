import os
import chardet
from loguru import logger
from PyQt5.QtWidgets import QMessageBox


class TextFileSync:
    """文本文件同步管理器"""
    
    MAX_TEXT_SIZE_BYTES = 1024 * 1024  # 最大文本大小限制：1 MB
    TEXT_FILE_ENCODING = 'utf-8'  # 默认编码
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1', 'ascii']
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setup_text_file_sync(self):
        """设置文本文件同步功能"""
        self.main_window.affirmation_text.textChanged.connect(self.on_affirmation_text_changed)
        
        from PyQt5.QtCore import QTimer
        self.main_window.text_save_timer = QTimer()
        self.main_window.text_save_timer.setSingleShot(True)
        self.main_window.text_save_timer.timeout.connect(self.save_text_to_file)
        
        logger.debug("文本文件同步功能已设置")

    def detect_file_encoding(self, file_path):
        """检测文件编码格式"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                if not raw_data:
                    return self.TEXT_FILE_ENCODING

                result = chardet.detect(raw_data)
                detected_encoding = result.get('encoding', self.TEXT_FILE_ENCODING)
                confidence = result.get('confidence', 0)

                logger.debug(f"检测到文件编码: {detected_encoding}, 置信度: {confidence}")

                if confidence < 0.7 or detected_encoding is None:
                    try:
                        raw_data.decode('utf-8')
                        return 'utf-8'
                    except UnicodeDecodeError:
                        pass

                    try:
                        raw_data.decode('gbk')
                        return 'gbk'
                    except UnicodeDecodeError:
                        pass

                    return self.TEXT_FILE_ENCODING

                return detected_encoding

        except Exception as e:
            logger.error(f"检测文件编码失败: {e}")
            return self.TEXT_FILE_ENCODING

    def load_text_from_file(self, file_path):
        """从文本文件加载内容到输入框"""
        logger.debug(f"开始加载文本文件: {file_path}")
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"文本文件不存在: {file_path}")
            if file_path:
                logger.debug(f"文本文件绝对路径: {os.path.abspath(file_path)}")
            return

        try:
            self.main_window.is_loading_text = True
            self.main_window.current_text_file = file_path

            encoding = self.detect_file_encoding(file_path)
            logger.info(f"加载文本文件: {file_path}, 编码: {encoding}")
            logger.debug(f"文本文件绝对路径: {os.path.abspath(file_path)}")
            logger.debug(f"文本文件大小: {os.path.getsize(file_path)} bytes")

            content = None
            encodings_to_try = [encoding] + [enc for enc in self.SUPPORTED_ENCODINGS if enc != encoding]

            for enc in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=enc, errors='replace') as f:
                        content = f.read()
                        logger.debug(f"成功使用编码 {enc} 读取文件")
                        break
                except Exception as e:
                    logger.debug(f"使用编码 {enc} 读取失败: {e}")
                    continue

            if content is None:
                raise Exception("无法使用任何支持的编码读取文件")

            content_bytes = content.encode(self.TEXT_FILE_ENCODING, errors='ignore')
            if len(content_bytes) > self.MAX_TEXT_SIZE_BYTES:
                safe_length = self.MAX_TEXT_SIZE_BYTES // 4
                content = content[:safe_length]
                logger.warning(f"文本内容超过最大大小限制({self.MAX_TEXT_SIZE_BYTES / 1024 / 1024:.1f}MB)，已截断")
                QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                                   self.main_window.tr(f"文本内容过大，已截断至安全长度"))

            self.main_window.affirmation_text.setText(content)

            logger.info(f"文本文件加载成功: {file_path}, 长度: {len(content)}")

        except PermissionError:
            logger.error(f"没有权限读取文件: {file_path}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                                self.main_window.tr(f"没有权限读取文件: {file_path}"))
        except Exception as e:
            logger.error(f"加载文本文件失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                                self.main_window.tr(f"加载文本文件失败: {str(e)}"))
        finally:
            self.main_window.is_loading_text = False

    def on_affirmation_text_changed(self, text):
        """肯定语文本变化时的回调"""
        if self.main_window.is_loading_text:
            return

        text_bytes = text.encode(self.TEXT_FILE_ENCODING, errors='ignore')
        if len(text_bytes) > self.MAX_TEXT_SIZE_BYTES:
            safe_length = self.MAX_TEXT_SIZE_BYTES // 4
            truncated_text = text[:safe_length]
            self.main_window.affirmation_text.setText(truncated_text)
            self.main_window.affirmation_text.setCursorPosition(len(truncated_text))
            logger.warning(f"输入文本超过最大大小限制({self.MAX_TEXT_SIZE_BYTES / 1024 / 1024:.1f}MB)，已截断")
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr(f"文本内容过大（超过1MB），已自动截断至安全长度"))
            return

        if self.main_window.current_text_file and os.path.exists(self.main_window.current_text_file):
            self.main_window.text_save_timer.stop()
            self.main_window.text_save_timer.start(500)

    def save_text_to_file(self):
        """将输入框内容保存到文本文件"""
        if not self.main_window.current_text_file:
            logger.debug("没有关联的文本文件，跳过保存")
            return

        logger.debug(f"开始保存文本到文件: {self.main_window.current_text_file}")

        try:
            text = self.main_window.affirmation_text.text()

            dir_path = os.path.dirname(self.main_window.current_text_file)
            if dir_path and not os.path.exists(dir_path):
                logger.debug(f"创建目录: {os.path.abspath(dir_path)}")
                os.makedirs(dir_path, exist_ok=True)

            with open(self.main_window.current_text_file, 'w', encoding=self.TEXT_FILE_ENCODING) as f:
                f.write(text)

            logger.debug(f"文本已保存到文件: {self.main_window.current_text_file}, 长度: {len(text)}")
            logger.debug(f"文本文件绝对路径: {os.path.abspath(self.main_window.current_text_file)}")
            logger.debug(f"保存后的文件大小: {os.path.getsize(self.main_window.current_text_file)} bytes")

        except PermissionError:
            logger.error(f"没有权限写入文件: {self.main_window.current_text_file}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                                self.main_window.tr(f"没有权限写入文件: {self.main_window.current_text_file}"))
        except Exception as e:
            logger.error(f"保存文本文件失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                                self.main_window.tr(f"保存文本文件失败: {str(e)}"))

    def set_text_file_path(self, file_path):
        """设置当前文本文件路径（用于程序化设置）"""
        if file_path and os.path.exists(file_path):
            self.main_window.text_file.setText(file_path)
            self.load_text_from_file(file_path)
        else:
            self.main_window.current_text_file = None
            self.main_window.text_file.clear()