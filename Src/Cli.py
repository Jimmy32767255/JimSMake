"""
SMake CLI 模块 - 命令行界面支持
在 GUI 启动失败或传入 -c/--cli 参数时启动
"""

import os
import sys
import argparse
from loguru import logger

# 添加父目录到路径以导入 Processors
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from Src.Processors.AudioCore import AudioCore
from Src.Processors.VideoCore import VideoCore


class SMakeCLI:
    """SMake 命令行界面"""

    def __init__(self):
        self.audio_processor = AudioCore()
        self.video_processor = VideoCore()

    def run(self, args=None):
        """运行CLI
        
        Args:
            args: 可以是参数列表(list)或已解析的argparse.Namespace对象
        """
        if args is None:
            args = sys.argv[1:]

        # 如果传入的是已解析的Namespace对象，直接使用
        if isinstance(args, argparse.Namespace):
            parsed_args = args
        else:
            # 否则解析参数列表
            parser = self._create_parser()
            parsed_args = parser.parse_args(args)

            if parsed_args.version:
                print("SMake CLI v1.0")
                return 0

            if not parsed_args.affirmation:
                print("错误: 必须指定肯定语音频文件 (-a/--affirmation)")
                parser.print_help()
                return 1

            if not parsed_args.output:
                print("错误: 必须指定输出文件路径 (-o/--output)")
                parser.print_help()
                return 1

        params = {
            'affirmation_file': parsed_args.affirmation,
            'output_path': parsed_args.output,
            'output_format': parsed_args.format.upper(),
            'background_file': parsed_args.background,
            'volume': parsed_args.volume,
            'background_volume': parsed_args.bg_volume,
            'frequency_mode': parsed_args.freq_mode,
            'speed': parsed_args.speed,
            'reverse': parsed_args.reverse,
            'overlay_times': parsed_args.overlay_times,
            'overlay_interval': parsed_args.overlay_interval,
            'volume_decrease': parsed_args.volume_decrease,
            'ensure_integrity': parsed_args.ensure_integrity,
            'metadata_title': parsed_args.title or '',
            'metadata_author': parsed_args.author or ''
        }

        logger.info("开始处理...")
        logger.info(f"肯定语: {params['affirmation_file']}")
        logger.info(f"输出: {params['output_path']}")
        if params['background_file']:
            logger.info(f"背景音: {params['background_file']}")

        # 设置音频处理器参数
        self.audio_processor.set_params(params)

        # 执行音频处理
        def progress_callback(progress):
            logger.info(f"进度: {progress}%")

        result = self.audio_processor.process(progress_callback=progress_callback)

        if result:
            logger.success(f"成功! 输出文件: {result}")

            # 如果需要生成视频
            if parsed_args.video and parsed_args.image:
                logger.info("开始生成视频...")
                video_path = os.path.splitext(result)[0] + '.mp4'

                video_params = {
                    'audio_path': result,
                    'video_image': parsed_args.image,
                    'video_output_path': video_path,
                    'video_resolution': parsed_args.resolution,
                    'metadata_title': params['metadata_title'],
                    'metadata_author': params['metadata_author']
                }
                self.video_processor.set_params(video_params)

                success = self.video_processor.generate_video(progress_callback=progress_callback)
                if success:
                    logger.success(f"视频生成成功: {video_path}")
                else:
                    logger.error("视频生成失败")

            return 0
        else:
            logger.error("处理失败!")
            return 1

    def _create_parser(self):
        """创建参数解析器"""
        parser = argparse.ArgumentParser(
            prog='smake',
            description='SMake - 潜意识音频生成器 (CLI模式)',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  python -m Src.Cli -a affirmation.wav -o output.wav
  python -m Src.Cli -a aff.wav -b bg.wav -o out.mp3 -f MP3
  python -m Src.Cli -a aff.wav -o out.wav --freq-mode 1 --speed 1.5
  python -m Src.Cli -a aff.wav -o out.wav -v image.jpg --video
            """
        )

        parser.add_argument('-a', '--affirmation', required=True,
                            help='肯定语音频文件路径 (WAV格式)')
        parser.add_argument('-o', '--output', required=True,
                            help='输出文件路径')
        parser.add_argument('-b', '--background',
                            help='背景音文件路径 (WAV格式)')
        parser.add_argument('-f', '--format', default='WAV',
                            choices=['WAV', 'MP3'],
                            help='输出格式 (默认: WAV)')

        parser.add_argument('--volume', type=float, default=-23.0,
                            help='肯定语音量调整 (dB, 默认: -23)')
        parser.add_argument('--bg-volume', type=float, default=0.0,
                            help='背景音量调整 (dB, 默认: 0)')

        parser.add_argument('--freq-mode', type=int, default=0,
                            choices=[0, 1, 2],
                            help='频率模式: 0=Raw, 1=UG(亚超声波), 2=传统(次声波) (默认: 0)')
        parser.add_argument('--speed', type=float, default=1.0,
                            help='倍速 (默认: 1.0)')
        parser.add_argument('--reverse', action='store_true',
                            help='倒放肯定语')

        parser.add_argument('--overlay-times', type=int, default=1,
                            help='叠加次数 (默认: 1)')
        parser.add_argument('--overlay-interval', type=float, default=1.0,
                            help='叠加间隔 (秒, 默认: 1.0)')
        parser.add_argument('--volume-decrease', type=float, default=0.0,
                            help='每次叠加音量递减 (dB, 默认: 0)')

        parser.add_argument('--ensure-integrity', action='store_true',
                            help='确保肯定语完整性')

        parser.add_argument('-v', '--image',
                            help='视觉化图片路径 (用于视频生成)')
        parser.add_argument('--video', action='store_true',
                            help='同时生成视频')
        parser.add_argument('--resolution', default='1920x1080',
                            help='视频分辨率 (默认: 1920x1080)')

        parser.add_argument('--title',
                            help='音频/视频标题元数据')
        parser.add_argument('--author',
                            help='音频/视频作者元数据')

        parser.add_argument('--version', action='store_true',
                            help='显示版本信息')

        return parser


def main():
    """CLI入口函数"""
    logger.remove()
    logger.add(sys.stderr, level="INFO",
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    cli = SMakeCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())
