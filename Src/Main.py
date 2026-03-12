import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale
from UI.Main_Window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序支持翻译
    translator = QTranslator()
    # 根据系统语言加载翻译文件
    locale = QLocale.system().name()
    
    # 构建翻译文件路径
    import os
    translation_dir = os.path.join(os.path.dirname(__file__), "..", "Translation")
    
    # 尝试加载翻译文件，支持多种语言
    translation_files = [
        os.path.join(translation_dir, f"{locale}.qm"),
        os.path.join(translation_dir, f"{locale.split('_')[0]}.qm"),
        os.path.join(translation_dir, "zh_CN.qm")
    ]
    
    translation_loaded = False
    for translation_file in translation_files:
        if os.path.exists(translation_file):
            if translator.load(translation_file):
                app.installTranslator(translator)
                print(f"已加载翻译文件: {translation_file}")
                translation_loaded = True
                break
    
    if not translation_loaded:
        print("未找到翻译文件，使用默认语言")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()