import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale
from UI.Main_Window import MainWindow
from loguru import logger

def main():
    app = QApplication(sys.argv)
    
    # 配置loguru日志
    logger.remove()  # 移除默认处理器
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    logger.info("应用程序启动")
    
    # 设置应用程序支持翻译
    translator = QTranslator()
    # 根据系统语言加载翻译文件
    locale = QLocale.system().name()
    logger.info(f"检测到系统语言: {locale}")
    
    # 构建翻译文件路径
    import os
    translation_dir = os.path.join(os.path.dirname(__file__), "..", "Translation")
    logger.debug(f"翻译文件目录: {translation_dir}")
    
    # 尝试加载翻译文件，支持多种语言
    translation_files = [
        os.path.join(translation_dir, f"{locale}.qm"),
        os.path.join(translation_dir, f"{locale.split('_')[0]}.qm"),
        os.path.join(translation_dir, "zh_CN.qm"),
        os.path.join(translation_dir, "en_US.qm"),
    ]
    
    logger.debug(f"尝试加载的翻译文件列表: {translation_files}")
    
    translation_loaded = False
    for translation_file in translation_files:
        if os.path.exists(translation_file):
            logger.debug(f"找到翻译文件: {translation_file}")
            if translator.load(translation_file):
                app.installTranslator(translator)
                logger.info(f"成功加载翻译文件: {translation_file}")
                translation_loaded = True
                break
            else:
                logger.warning(f"加载翻译文件失败: {translation_file}")
        else:
            logger.debug(f"翻译文件不存在: {translation_file}")
    
    if not translation_loaded:
        logger.warning("未找到可用的翻译文件，使用默认语言")
    
    window = MainWindow()
    window.show()
    
    logger.info("应用程序界面已显示，进入事件循环")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()