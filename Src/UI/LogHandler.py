import os
from loguru import logger
from PyQt5.QtCore import QTimer


class LogHandler:
    """日志处理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setup_log_handler(self):
        """设置日志处理器，将日志输出到UI"""
        
        class UILogHandler:
            """自定义日志处理器，将日志发送到UI"""
            def __init__(self, main_window):
                self.main_window = main_window

            def write(self, message):
                """写入日志消息"""
                clean_message = message.strip()
                if clean_message:
                    QTimer.singleShot(0, lambda msg=clean_message: 
                        self.main_window.append_log_message(msg))

            def flush(self):
                pass

        self.main_window.ui_log_handler = UILogHandler(self.main_window)
        logger.add(self.main_window.ui_log_handler, 
                   format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", 
                   level="DEBUG")
        
        self._display_cached_logs()
        
        logger.info("UI日志处理器已设置")

    def _display_cached_logs(self):
        """显示UI初始化之前缓存的日志"""
        log_file = os.path.join(os.path.dirname(__file__), "..", "..", "SMake.log")
        log_file = os.path.abspath(log_file)
        
        if os.path.exists(log_file) and hasattr(self.main_window, 'log_text_edit'):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    for line in last_lines:
                        line = line.strip()
                        if line:
                            self.main_window.log_text_edit.append(line)
                    
                    if last_lines:
                        self.main_window.log_text_edit.append("-" * 80)
                        self.main_window.log_text_edit.append("[历史日志结束，以下为实时日志]")
                        self.main_window.log_text_edit.append("")
                        
            except Exception as e:
                logger.error(f"读取历史日志失败: {e}")