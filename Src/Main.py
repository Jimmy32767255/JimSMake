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
    if translator.load(f"smake_{locale}"):
        app.installTranslator(translator)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()