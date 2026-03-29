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

    # 动态枚举所有可用的翻译文件
    available_translations = {}
    if os.path.exists(translation_dir):
        for filename in os.listdir(translation_dir):
            if filename.endswith('.qm'):
                # 从文件名提取语言代码 (如 zh_CN.qm -> zh_CN)
                lang_code = filename[:-3]  # 移除 .qm 后缀
                file_path = os.path.join(translation_dir, filename)
                available_translations[lang_code] = file_path
                logger.debug(f"发现翻译文件: {lang_code} -> {file_path}")

    logger.info(f"可用翻译文件: {list(available_translations.keys())}")

    # 尝试按优先级加载翻译文件
    translation_loaded = False

    # 优先级1: 系统语言完整匹配 (如 zh_CN)
    if locale in available_translations:
        translation_file = available_translations[locale]
        logger.debug(f"尝试加载系统语言翻译: {translation_file}")
        if translator.load(translation_file):
            app.installTranslator(translator)
            logger.info(f"成功加载翻译文件: {translation_file}")
            translation_loaded = True

    # 优先级2: 系统语言前缀匹配 (如 zh_CN -> zh)
    if not translation_loaded:
        locale_prefix = locale.split('_')[0]
        for lang_code, file_path in available_translations.items():
            if lang_code.startswith(locale_prefix):
                logger.debug(f"尝试加载语言前缀匹配: {file_path}")
                if translator.load(file_path):
                    app.installTranslator(translator)
                    logger.info(f"成功加载翻译文件: {file_path}")
                    translation_loaded = True
                    break

    # 优先级3: 默认语言 (zh_CN)
    if not translation_loaded and 'zh_CN' in available_translations:
        translation_file = available_translations['zh_CN']
        logger.debug(f"尝试加载默认语言: {translation_file}")
        if translator.load(translation_file):
            app.installTranslator(translator)
            logger.info(f"成功加载默认翻译文件: {translation_file}")
            translation_loaded = True

    # 优先级4: 任意可用翻译
    if not translation_loaded and available_translations:
        for lang_code, file_path in available_translations.items():
            logger.debug(f"尝试加载可用翻译: {file_path}")
            if translator.load(file_path):
                app.installTranslator(translator)
                logger.info(f"成功加载翻译文件: {file_path}")
                translation_loaded = True
                break

    if not translation_loaded:
        logger.warning("未找到可用的翻译文件，使用默认语言")
    
    window = MainWindow()
    window.show()
    
    logger.info("应用程序界面已显示，进入事件循环")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()