import sys
import os
import argparse
from loguru import logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog='smake',
        description='SMake - 潜意识音频生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
运行模式:
  默认启动GUI界面
  -c, --cli     启动CLI模式
  -h, --help    显示帮助信息

CLI模式示例:
  python -m Src.Main --cli -a affirmation.wav -o output.wav
  python -m Src.Main -c -a aff.wav -b bg.wav -o out.mp3 -f MP3
        """
    )

    parser.add_argument('-c', '--cli', action='store_true',
                        help='启动CLI模式（命令行界面）')

    # CLI 参数（仅在 --cli 模式下使用）
    parser.add_argument('-a', '--affirmation',
                        help='CLI: 肯定语音频文件路径 (WAV格式)')
    parser.add_argument('-o', '--output',
                        help='CLI: 输出文件路径')
    parser.add_argument('-b', '--background',
                        help='CLI: 背景音文件路径 (WAV格式)')
    parser.add_argument('-f', '--format', default='WAV',
                        choices=['WAV', 'MP3'],
                        help='CLI: 输出格式 (默认: WAV)')
    parser.add_argument('--volume', type=float, default=-23.0,
                        help='CLI: 肯定语音量调整 (dB, 默认: -23)')
    parser.add_argument('--bg-volume', type=float, default=0.0,
                        help='CLI: 背景音量调整 (dB, 默认: 0)')
    parser.add_argument('--freq-mode', type=int, default=0,
                        choices=[0, 1, 2],
                        help='CLI: 频率模式: 0=Raw, 1=UG(亚超声波), 2=传统(次声波) (默认: 0)')
    parser.add_argument('--speed', type=float, default=1.0,
                        help='CLI: 倍速 (默认: 1.0)')
    parser.add_argument('--reverse', action='store_true',
                        help='CLI: 倒放肯定语')
    parser.add_argument('--overlay-times', type=int, default=1,
                        help='CLI: 叠加次数 (默认: 1)')
    parser.add_argument('--overlay-interval', type=float, default=1.0,
                        help='CLI: 叠加间隔 (秒, 默认: 1.0)')
    parser.add_argument('--volume-decrease', type=float, default=0.0,
                        help='CLI: 每次叠加音量递减 (dB, 默认: 0)')
    parser.add_argument('--ensure-integrity', action='store_true',
                        help='CLI: 确保肯定语完整性')
    parser.add_argument('-v', '--image',
                        help='CLI: 视觉化图片路径 (用于视频生成)')
    parser.add_argument('--video', action='store_true',
                        help='CLI: 同时生成视频')
    parser.add_argument('--resolution', default='1920x1080',
                        help='CLI: 视频分辨率 (默认: 1920x1080)')
    parser.add_argument('--title',
                        help='CLI: 音频/视频标题元数据')
    parser.add_argument('--author',
                        help='CLI: 音频/视频作者元数据')
    parser.add_argument('--version', action='store_true',
                        help='显示版本信息')
    parser.add_argument('--log-level', default='INFO',
                        choices=['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='设置日志级别 (默认: INFO)')

    return parser.parse_args()


def run_cli(args):
    """运行CLI模式"""
    from Cli import SMakeCLI

    cli = SMakeCLI()

    if args.version:
        print("SMake v1.0")
        return 0

    if not args.affirmation:
        print("错误: CLI模式需要指定肯定语音频文件 (-a/--affirmation)")
        print("使用 --help 查看帮助信息")
        return 1

    if not args.output:
        print("错误: CLI模式需要指定输出文件路径 (-o/--output)")
        print("使用 --help 查看帮助信息")
        return 1

    logger.debug(f"run_cli - affirmation: {args.affirmation}")
    logger.debug(f"run_cli - affirmation绝对路径: {os.path.abspath(args.affirmation)}")
    logger.debug(f"run_cli - affirmation是否存在: {os.path.exists(args.affirmation)}")
    logger.debug(f"run_cli - output: {args.output}")
    logger.debug(f"run_cli - output绝对路径: {os.path.abspath(args.output)}")
    output_dir = os.path.dirname(args.output)
    logger.debug(f"run_cli - output_dir: {output_dir}")
    logger.debug(f"run_cli - output_dir绝对路径: {os.path.abspath(output_dir) if output_dir else 'None'}")
    logger.debug(f"run_cli - output_dir是否存在: {os.path.exists(output_dir) if output_dir else False}")
    if args.background:
        logger.debug(f"run_cli - background: {args.background}")
        logger.debug(f"run_cli - background绝对路径: {os.path.abspath(args.background)}")
        logger.debug(f"run_cli - background是否存在: {os.path.exists(args.background)}")

    # 直接传递已解析的args对象，避免手动参数转换
    return cli.run(args)


def get_resource_path():
    """获取资源路径，支持打包版本和开发版本"""
    import os

    if getattr(sys, 'frozen', False):
        # 打包版本：使用 PyInstaller 的 _MEIPASS
        resource_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        logger.debug(f"获取资源路径(打包版本): {resource_path}")
        logger.debug(f"资源路径绝对路径: {os.path.abspath(resource_path)}")
        logger.debug(f"资源路径是否存在: {os.path.exists(resource_path)}")
        return resource_path
    else:
        # 开发版本：使用项目根目录
        resource_path = os.path.join(os.path.dirname(__file__), "..")
        logger.debug(f"获取资源路径(开发版本): {resource_path}")
        logger.debug(f"资源路径绝对路径: {os.path.abspath(resource_path)}")
        logger.debug(f"资源路径是否存在: {os.path.exists(resource_path)}")
        return resource_path


def run_gui():
    """运行GUI模式"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTranslator, QLocale
    from UI.Main_Window import MainWindow

    app = QApplication(sys.argv)

    translator = QTranslator()
    locale = QLocale.system().name()
    logger.info(f"检测到系统语言: {locale}")

    import os
    # 使用统一的资源路径获取函数
    base_dir = get_resource_path()
    translation_dir = os.path.join(base_dir, "Translation")
    logger.debug(f"翻译文件目录: {translation_dir}")
    logger.debug(f"翻译文件目录绝对路径: {os.path.abspath(translation_dir)}")
    logger.debug(f"翻译文件目录是否存在: {os.path.exists(translation_dir)}")
    logger.debug(f"基础目录: {base_dir}, 是否打包: {getattr(sys, 'frozen', False)}")

    available_translations = {}
    if os.path.exists(translation_dir):
        try:
            translation_files = os.listdir(translation_dir)
            logger.debug(f"翻译目录内容: {translation_files}")
            for filename in translation_files:
                if filename.endswith('.qm'):
                    lang_code = filename[:-3]
                    file_path = os.path.join(translation_dir, filename)
                    available_translations[lang_code] = file_path
                    logger.debug(f"发现翻译文件: {lang_code} -> {file_path}")
                    logger.debug(f"翻译文件绝对路径: {os.path.abspath(file_path)}")
                    logger.debug(f"翻译文件大小: {os.path.getsize(file_path)} bytes")
        except Exception as e:
            logger.error(f"读取翻译目录失败: {e}")

    logger.info(f"可用翻译文件: {list(available_translations.keys())}")

    translation_loaded = False

    if locale in available_translations:
        translation_file = available_translations[locale]
        logger.debug(f"尝试加载系统语言翻译: {translation_file}")
        if translator.load(translation_file):
            app.installTranslator(translator)
            logger.info(f"成功加载翻译文件: {translation_file}")
            translation_loaded = True

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

    if not translation_loaded and 'zh_CN' in available_translations:
        translation_file = available_translations['zh_CN']
        logger.debug(f"尝试加载默认语言: {translation_file}")
        if translator.load(translation_file):
            app.installTranslator(translator)
            logger.info(f"成功加载默认翻译文件: {translation_file}")
            translation_loaded = True

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

    return app.exec_()


def main():
    """主入口函数"""
    # 先解析参数以获取日志级别
    args = parse_args()

    logger.remove()
    try:
        # 始终添加文件日志处理器（./SMake.log）
        log_path = os.path.join(os.path.dirname(__file__), "..", "SMake.log")
        log_path = os.path.abspath(log_path)
        # 确保日志目录存在
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        logger.add(log_path, level=args.log_level, rotation="10 MB", encoding="utf-8",
                   format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
        logger.debug(f"日志文件路径: {log_path}")

        # 如果有控制台，同时添加 stderr 日志处理器
        if sys.stderr is not None:
            logger.add(sys.stderr, level=args.log_level,
                       format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    except Exception:
        # 如果添加日志处理器失败，静默处理
        pass

    logger.info(f"应用程序启动，日志级别: {args.log_level}")

    if args.version:
        print("SMake v1.0")
        return 0

    if args.cli:
        logger.info("启动CLI模式")
        return run_cli(args)

    logger.info("尝试启动GUI模式")

    try:
        return run_gui()
    except ImportError as e:
        logger.warning(f"GUI启动失败，缺少依赖: {e}")
        print(f"\n无法启动GUI模式: {e}")
        print("正在切换到CLI模式...\n")

        if args.affirmation and args.output:
            return run_cli(args)
        else:
            print("CLI模式需要以下参数:")
            print("  -a, --affirmation   肯定语音频文件路径")
            print("  -o, --output        输出文件路径")
            print("\n使用 --help 查看完整帮助信息")
            return 1
    except Exception as e:
        logger.error(f"GUI启动失败: {e}")
        print(f"\nGUI启动失败: {e}")
        print("正在切换到CLI模式...\n")

        if args.affirmation and args.output:
            return run_cli(args)
        else:
            print("CLI模式需要以下参数:")
            print("  -a, --affirmation   肯定语音频文件路径")
            print("  -o, --output        输出文件路径")
            print("\n使用 --help 查看完整帮助信息")
            return 1


if __name__ == '__main__':
    sys.exit(main())
