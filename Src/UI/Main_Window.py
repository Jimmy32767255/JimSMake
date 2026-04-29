from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton,
                             QSlider, QCheckBox, QFileDialog, QSpinBox, QDoubleSpinBox,
                             QScrollArea, QGridLayout, QMessageBox, QTabWidget, QProgressDialog,
                             QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QTranslator, QSettings, QThread, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices
import pyttsx3
import pyaudio
import wave
import os
import chardet
import subprocess
import sys
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from Processors.AudioProcessor import AudioProcessor
from Processors.VideoProcessor import VideoProcessor

from .AudioRecorder import AudioRecorder
from .LogHandler import LogHandler
from .TextFileSync import TextFileSync
from .ProjectManager import ProjectManager

class MainWindow(QMainWindow):
    # 文本文件相关常量
    MAX_TEXT_SIZE_BYTES = 1024 * 1024  # 最大文本大小限制：1 MB
    TEXT_FILE_ENCODING = 'utf-8'  # 默认编码
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1', 'ascii']

    def __init__(self):
        super().__init__()
        logger.info("初始化主窗口")

        # 初始化设置
        self.settings = QSettings("JimSMake", "SMake")
        self.current_language = self.settings.value("language", "zh_CN")
        self.current_project_group = self.settings.value("current_project_group", self.tr("默认项目组"))
        self.current_project_name = self.settings.value("current_project", "")
        logger.info(f"加载设置，当前语言: {self.current_language}, 当前项目组: {self.current_project_group}, 当前项目: {self.current_project_name}")

        # 初始化录音相关变量
        self.recorder = None
        self.is_recording = False

        # 初始化文本文件相关变量
        self.current_text_file = None  # 当前关联的文本文件路径
        self.is_loading_text = False   # 防止循环更新的标志
        self.text_save_timer = None    # 延迟保存定时器

        # 检测ffmpeg是否可用
        self.ffmpeg_available = self.check_ffmpeg_available()

        self.initUI()
        self.setupTranslations()
        self.enumerate_tts_engines()
        self.enumerate_audio_devices()
        
        # 初始化文本文件同步处理器
        self.text_sync = TextFileSync(self)
        self.text_sync.setup_text_file_sync()
        
        # 初始化日志处理器
        self.log_handler = LogHandler(self)
        self.log_handler.setup_log_handler()

        # UI初始化完成后，如果当前有项目，自动加载资源
        if hasattr(self, 'current_project_name') and self.current_project_name:
            project_dir = self.get_current_project_dir()
            if project_dir:
                logger.info(f"UI初始化完成，自动加载项目资源: {project_dir}")
                self.load_project_resources(project_dir)

        logger.info("主窗口初始化完成")

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        logger.info("主窗口关闭，进行清理")

        # 如果进度对话框存在，先断开信号再关闭
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            try:
                self.progress_dialog.canceled.disconnect(self.cancel_generation)
            except:
                pass  # 信号可能已经被断开
            self.progress_dialog.close()
            self.progress_dialog = None

        # 如果有正在运行的音频处理器，取消它
        if hasattr(self, 'audio_processor') and self.audio_processor and self.audio_processor.isRunning():
            self.audio_processor.cancel()
            self.audio_processor.wait(1000)  # 等待最多1秒

        # 如果有正在进行的录音，停止它
        if hasattr(self, 'recorder') and self.recorder and self.recorder.isRunning():
            self.recorder.stop()
            self.recorder.wait(1000)

        event.accept()

    def check_ffmpeg_available(self):
        """检测ffmpeg是否可用"""
        try:
            # 可能的ffmpeg可执行文件名
            ffmpeg_names = ['ffmpeg.exe', 'ffmpeg'] if sys.platform == 'win32' else ['ffmpeg']

            # 检查系统PATH
            for name in ffmpeg_names:
                try:
                    result = subprocess.run(['where', name] if sys.platform == 'win32' else ['which', name],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        ffmpeg_path = result.stdout.strip().split('\n')[0].strip()
                        if ffmpeg_path:
                            logger.info(f"检测到ffmpeg: {ffmpeg_path}")
                            return True
                except Exception:
                    pass

            # 尝试直接调用ffmpeg
            for name in ffmpeg_names:
                try:
                    result = subprocess.run([name, '-version'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        logger.info(f"检测到ffmpeg: {name}")
                        return True
                except Exception:
                    pass

            logger.warning("未检测到ffmpeg，视频生成和非WAV音频格式功能将被禁用")
            return False
        except Exception as e:
            logger.error(f"检测ffmpeg时出错: {e}")
            return False

    def update_ui_for_ffmpeg_availability(self):
        """根据ffmpeg可用性更新UI控件状态"""
        if self.ffmpeg_available:
            return

        logger.info("ffmpeg不可用，禁用相关功能")

        # 显示警告标签
        if hasattr(self, 'ffmpeg_warning_label'):
            self.ffmpeg_warning_label.setVisible(True)

        # 禁用视频生成功能
        if hasattr(self, 'generate_video'):
            self.generate_video.setChecked(False)
            self.generate_video.setEnabled(False)
            self.generate_video.setToolTip(self.tr("需要安装ffmpeg才能使用此功能"))

        # 禁用视频设置组
        if hasattr(self, 'video_group'):
            self.video_group.setEnabled(False)

        # 限制音频格式为WAV
        if hasattr(self, 'audio_format'):
            # 清除所有选项，只保留WAV
            self.audio_format.clear()
            self.audio_format.addItem("WAV")
            self.audio_format.setEnabled(False)
            self.audio_format.setToolTip(self.tr("需要安装ffmpeg才能使用其他音频格式"))

        # 更新提示文本
        if hasattr(self, 'selection_hint'):
            self.selection_hint.setText(self.tr("* 必须至少选择生成音频或生成视频一项（当前仅支持音频生成）"))

        # 更新文件选择对话框的过滤器，只允许选择WAV文件
        if hasattr(self, 'btn_browse_aff'):
            # 断开原有连接并重新连接，使用WAV-only过滤器
            try:
                self.btn_browse_aff.clicked.disconnect()
            except:
                pass
            self.btn_browse_aff.clicked.connect(lambda: self.browse_file(self.affirmation_file,
                                                                         self.tr("WAV音频文件 (*.wav)")))
            self.btn_browse_aff.setToolTip(self.tr("选择WAV格式的音频文件（需要ffmpeg才能使用其他格式）"))

        if hasattr(self, 'btn_browse_bg'):
            # 断开原有连接并重新连接，使用WAV-only过滤器
            try:
                self.btn_browse_bg.clicked.disconnect()
            except:
                pass
            self.btn_browse_bg.clicked.connect(lambda: self.browse_file(self.background_file,
                                                                        self.tr("WAV音频文件 (*.wav)")))
            self.btn_browse_bg.setToolTip(self.tr("选择WAV格式的音频文件（需要ffmpeg才能使用其他格式）"))

    def get_resource_path(self):
        """获取资源路径，支持打包版本和开发版本"""
        import sys

        if getattr(sys, 'frozen', False):
            # 打包版本：优先使用可执行文件所在目录，便于用户自定义资源
            exe_dir = os.path.dirname(sys.executable)
            # 检查可执行文件所在目录是否有 Translation 文件夹
            if os.path.exists(os.path.join(exe_dir, "Translation")):
                return exe_dir
            # 否则使用 PyInstaller 的 _MEIPASS 临时目录
            return getattr(sys, '_MEIPASS', exe_dir)
        else:
            # 开发版本：使用项目根目录
            return os.path.join(os.path.dirname(__file__), "..", "..")

    def setupTranslations(self):
        """设置翻译支持"""
        logger.info(f"开始设置翻译支持，当前语言: {self.current_language}")

        # 移除现有的翻译器
        app = QApplication.instance()
        if hasattr(self, 'translator') and self.translator:
            logger.debug("移除现有翻译器")
            app.removeTranslator(self.translator)

        # 创建新的翻译器
        self.translator = QTranslator()

        # 构建翻译文件路径
        base_dir = self.get_resource_path()
        translation_dir = os.path.join(base_dir, "Translation")
        logger.debug(f"翻译文件目录: {translation_dir}")
        logger.debug(f"基础目录: {base_dir}, 是否打包: {getattr(sys, 'frozen', False)}")
        
        # 根据当前语言设置加载翻译文件
        translation_file = os.path.join(translation_dir, f"{self.current_language}.qm")
        logger.debug(f"尝试加载翻译文件: {translation_file}")
        
        if os.path.exists(translation_file):
            if self.translator.load(translation_file):
                app.installTranslator(self.translator)
                logger.info(f"成功加载翻译文件: {translation_file}")
            else:
                logger.error(f"加载翻译文件失败: {translation_file}")
        else:
            logger.warning(f"翻译文件不存在: {translation_file}")
            
        # 更新UI文本
        logger.debug("开始更新UI文本翻译")
        self.retranslateUI()
        logger.info("翻译设置完成")
        
    def retranslateUI(self):
        """重新翻译UI文本"""
        logger.debug("开始重新翻译UI文本")

        if hasattr(self, 'tab_widget'):
            # 更新选项卡标题
            if hasattr(self, 'project_tab_index'):
                self.tab_widget.setTabText(self.project_tab_index, self.tr("项目"))
            if hasattr(self, 'affirmation_tab_index'):
                self.tab_widget.setTabText(self.affirmation_tab_index, self.tr("肯定语"))
            if hasattr(self, 'background_tab_index'):
                self.tab_widget.setTabText(self.background_tab_index, self.tr("背景音"))
            if hasattr(self, 'freq_track_tab_index'):
                self.tab_widget.setTabText(self.freq_track_tab_index, self.tr("特定频率音轨"))
            if hasattr(self, 'output_tab_index'):
                self.tab_widget.setTabText(self.output_tab_index, self.tr("输出"))
            if hasattr(self, 'settings_tab_index'):
                self.tab_widget.setTabText(self.settings_tab_index, self.tr("设置"))
            if hasattr(self, 'log_tab_index'):
                self.tab_widget.setTabText(self.log_tab_index, self.tr("日志"))
            logger.debug("选项卡标题翻译完成")

        # 更新窗口标题
        self.setWindowTitle(self.tr("SMake"))
        logger.debug("窗口标题翻译完成")

        # 更新肯定语组
        if hasattr(self, 'affirmation_group'):
            self.affirmation_group.setTitle(self.tr("肯定语"))
            self.label_audio_file.setText(self.tr("音频文件:"))
            self.affirmation_file.setToolTip(self.tr("选择一个音频文件作为肯定语。"))
            self.btn_browse_aff.setText(self.tr("浏览..."))
            self.btn_browse_aff.setToolTip(self.tr("选择音频文件"))
            self.label_affirmation_text.setText(self.tr("肯定语:"))
            self.affirmation_text.setToolTip(self.tr("输入肯定语。"))
            self.label_text_file.setText(self.tr("文本文件:"))
            self.text_file.setToolTip(self.tr("选择一个文本文件作为肯定语。"))
            self.btn_browse_text.setText(self.tr("浏览..."))
            self.btn_browse_text.setToolTip(self.tr("选择文本文件"))
            self.label_tts_engine.setText(self.tr("TTS引擎:"))
            self.tts_engine.setToolTip(self.tr("选择从文本生成肯定语音频时要使用的TTS引擎。"))
            self.generate_tts_btn.setText(self.tr("生成"))
            self.generate_tts_btn.setToolTip(self.tr("通过TTS从文本生成肯定语。"))
            self.label_record_device.setText(self.tr("录制设备:"))
            self.record_device.setToolTip(self.tr("选择录制肯定语音频时要使用的设备。"))
            if not self.is_recording:
                self.record_btn.setText(self.tr("开始录制"))
            self.record_btn.setToolTip(self.tr("开始/停止录制肯定语。"))
            self.label_volume.setText(self.tr("音量:"))
            self.affirmation_volume.setToolTip(self.tr("改变肯定语音轨的音量。（单位为分贝）"))
            self.label_freq_mode.setText(self.tr("频率模式:"))
            self.frequency_mode.setItemText(0, self.tr("Raw（保持不变）"))
            self.frequency_mode.setItemText(1, self.tr("UG（亚超声波）"))
            self.frequency_mode.setItemText(2, self.tr("传统（次声波）"))
            self.frequency_mode.setToolTip(self.tr("改变肯定语音轨的频率，推荐使用地下（UG）模式。"))
            self.label_speed.setText(self.tr("倍速:"))
            self.speed_slider.setToolTip(self.tr("改变肯定语音轨的倍速。"))
            self.reverse_check.setText(self.tr("倒放"))
            self.reverse_check.setToolTip(self.tr("肯定语是否倒放。"))
            self.overlay_group.setTitle(self.tr("叠加设置"))
            self.label_overlay_times.setText(self.tr("叠加次数:"))
            self.overlay_times.setToolTip(self.tr("肯定语音轨的叠加次数。"))
            self.label_overlay_interval.setText(self.tr("间隔:"))
            self.overlay_interval.setToolTip(self.tr("每次叠加后，下一个叠加音轨应比上一个延后多少时间？"))
            self.label_volume_decrease.setText(self.tr("音量递减:"))
            self.volume_decrease.setToolTip(self.tr("每次叠加后，下一个叠加音轨应比上一个音量降低多少？"))
            
            # 更新确保肯定语完整性复选框
            if hasattr(self, 'ensure_integrity_check'):
                self.ensure_integrity_check.setText(self.tr("确保肯定语完整性"))
                self.ensure_integrity_check.setToolTip(self.tr("启用后，肯定语将在背景音乐中完整循环播放，不会被截断。如果肯定语比背景音乐长，将阻止生成。"))

        # 更新背景音组
        if hasattr(self, 'background_group'):
            self.background_group.setTitle(self.tr("背景音"))
            self.label_bg_file.setText(self.tr("背景音文件:"))
            self.background_file.setToolTip(self.tr("选择一个音频文件作为背景音。"))
            self.btn_browse_bg.setText(self.tr("浏览..."))
            self.btn_browse_bg.setToolTip(self.tr("选择背景音频文件"))
            self.label_bg_volume.setText(self.tr("音量:"))
            self.background_volume.setToolTip(self.tr("改变背景音音轨的音量。（单位为分贝）"))

        # 更新特定频率音轨组
        if hasattr(self, 'freq_track_group'):
            self.freq_track_group.setTitle(self.tr("特定频率音轨"))
            self.freq_track_enabled.setText(self.tr("启用特定频率音轨"))
            self.freq_track_enabled.setToolTip(self.tr("在音频中叠加特定频率的音轨。"))
            self.label_freq_track_freq.setText(self.tr("频率 (Hz):"))
            self.freq_track_freq.setToolTip(self.tr("选择或输入要叠加的特定频率(Hz)。"))
            self.label_freq_track_volume.setText(self.tr("音量 (dB):"))
            self.freq_track_volume.setToolTip(self.tr("特定频率音轨的音量（分贝）。"))

        # 更新输出组
        if hasattr(self, 'output_group'):
            self.output_group.setTitle(self.tr("输出"))
            self.generate_audio.setText(self.tr("生成音频"))
            self.generate_audio.setToolTip(self.tr("是否生成音频。"))
            self.audio_group.setTitle(self.tr("音频设置"))
            self.label_audio_format.setText(self.tr("格式:"))
            self.label_audio_sample_rate.setText(self.tr("采样率:"))
            # 更新ffmpeg警告标签
            if hasattr(self, 'ffmpeg_warning_label'):
                self.ffmpeg_warning_label.setText(self.tr("⚠️ 未检测到ffmpeg，视频生成和非WAV音频格式功能已被禁用"))
            self.generate_video.setText(self.tr("生成视频"))
            self.generate_video.setToolTip(self.tr("是否生成视频。"))
            self.video_group.setTitle(self.tr("视频设置"))
            self.label_video_image.setText(self.tr("视觉化图片:"))
            self.video_image.setToolTip(self.tr("选择一个图片文件作为视觉化。"))
            self.btn_browse_image.setText(self.tr("浏览..."))
            self.btn_browse_image.setToolTip(self.tr("选择视觉化图片"))
            self.label_search_keyword.setText(self.tr("搜索关键词:"))
            self.search_keyword.setToolTip(self.tr("输入关键词。"))
            self.label_search_engine.setText(self.tr("搜索引擎:"))
            self.search_engine.setToolTip(self.tr("搜索视觉化图片时使用的搜索引擎。"))
            self.search_btn.setText(self.tr("联机搜索"))
            self.search_btn.setToolTip(self.tr("联机搜索视觉化图片。"))
            self.label_video_format.setText(self.tr("视频格式:"))
            self.label_video_audio_sample_rate.setText(self.tr("音频采样率:"))
            self.label_video_bitrate.setText(self.tr("码率:"))
            self.label_video_resolution.setText(self.tr("分辨率:"))
            self.selection_hint.setText(self.tr("* 必须至少选择生成音频或生成视频一项"))
            self.metadata_group.setTitle(self.tr("元数据"))
            self.label_metadata_title.setText(self.tr("标题:"))
            self.metadata_title.setToolTip(self.tr("设置项目输出元数据中的标题。"))
            self.label_metadata_author.setText(self.tr("作者:"))
            self.metadata_author.setToolTip(self.tr("设置项目输出元数据中的作者。"))
            self.generate_btn.setText(self.tr("生成项目"))
            self.generate_btn.setToolTip(self.tr("开始生成项目！"))
            # 预览组
            if hasattr(self, 'preview_group'):
                self.preview_group.setTitle(self.tr("预览"))
                self.preview_zoom_in_btn.setText(self.tr("放大"))
                self.preview_zoom_in_btn.setToolTip(self.tr("放大预览视图"))
                self.preview_zoom_out_btn.setText(self.tr("缩小"))
                self.preview_zoom_out_btn.setToolTip(self.tr("缩小预览视图"))
                self.preview_reset_btn.setText(self.tr("重置视图"))
                self.preview_reset_btn.setToolTip(self.tr("重置预览视图缩放和位置"))
                self.preview_update_btn.setText(self.tr("更新预览"))
                self.preview_update_btn.setToolTip(self.tr("根据当前配置更新预览"))
                self.preview_tracks_label.setText(self.tr('轨道预览（点击"更新预览"查看）'))
                self.preview_zoom_label.setText(self.tr("缩放: 100%"))

        # 更新设置组
        if hasattr(self, 'settings_group'):
            self.settings_group.setTitle(self.tr("设置"))
            self.label_language.setText(self.tr("语言:"))
            self.apply_language_btn.setText(self.tr("应用语言"))
            self.reset_settings_btn.setText(self.tr("重置设置"))
            self.about_group.setTitle(self.tr("关于"))
            self.about_label.setText(self.tr("SMake"))

        # 更新日志组
        if hasattr(self, 'log_group'):
            self.log_group.setTitle(self.tr("日志输出"))
            self.clear_log_btn.setText(self.tr("清空日志"))
            self.clear_log_btn.setToolTip(self.tr("清空日志显示区域"))

        # 更新项目组
        if hasattr(self, 'project_group'):
            self.project_group.setTitle(self.tr("项目管理"))
            # 项目组相关
            self.label_current_project_group.setText(self.tr("当前项目组:"))
            if not hasattr(self, 'current_project_group') or not self.current_project_group:
                self.current_project_group_label.setText(self.tr("未选择项目组"))
            self.label_project_group_list.setText(self.tr("项目组列表:"))
            self.project_group_list.setToolTip(self.tr("选择或切换当前项目组"))
            self.label_new_project_group.setText(self.tr("新建项目组:"))
            if hasattr(self, 'new_project_group_name'):
                self.new_project_group_name.setToolTip(self.tr("输入新项目组名称"))
                self.new_project_group_name.setPlaceholderText(self.tr("输入项目组名称"))
            self.create_project_group_btn.setText(self.tr("创建项目组"))
            self.create_project_group_btn.setToolTip(self.tr("创建新项目组"))
            self.delete_project_group_btn.setText(self.tr("删除项目组"))
            self.delete_project_group_btn.setToolTip(self.tr("删除选中的项目组"))
            # 项目相关
            self.label_current_project.setText(self.tr("当前项目:"))
            if not hasattr(self, 'current_project_name') or not self.current_project_name:
                self.current_project_label.setText(self.tr("未选择项目"))
            self.label_project_list.setText(self.tr("项目列表:"))
            self.project_list.setToolTip(self.tr("选择或切换当前项目"))
            self.refresh_projects_btn.setText(self.tr("刷新"))
            self.refresh_projects_btn.setToolTip(self.tr("刷新项目列表"))
            self.label_new_project.setText(self.tr("新建项目:"))
            if hasattr(self, 'new_project_name'):
                self.new_project_name.setToolTip(self.tr("输入新项目名称"))
                self.new_project_name.setPlaceholderText(self.tr("输入项目名称"))
            self.create_project_btn.setText(self.tr("创建项目"))
            self.create_project_btn.setToolTip(self.tr("创建新项目"))
            self.delete_project_btn.setText(self.tr("删除项目"))
            self.delete_project_btn.setToolTip(self.tr("删除选中的项目"))
            self.label_project_path.setText(self.tr("项目路径:"))
            # 导入导出相关
            if hasattr(self, 'label_import_export'):
                self.label_import_export.setText(self.tr("导入/导出:"))
                self.export_project_btn.setText(self.tr("导出项目"))
                self.export_project_btn.setToolTip(self.tr("将当前项目导出为压缩文件"))
                self.export_project_group_btn.setText(self.tr("导出项目组"))
                self.export_project_group_btn.setToolTip(self.tr("将当前项目组导出为压缩文件"))
                self.import_btn.setText(self.tr("导入"))
                self.import_btn.setToolTip(self.tr("从压缩文件导入项目或项目组"))
            # 项目结构
            self.project_structure_group.setTitle(self.tr("项目结构"))
            self.project_structure_label.setText(
                self.tr("项目组名称/\n"
                       "  └── 项目名称/\n"
                       "      ├── README.md (项目描述)\n"
                       "      ├── config.json (项目配置)\n"
                       "      ├── Assets/ (资产)\n"
                       "      │   ├── BGM.wav (背景音乐)\n"
                       "      │   ├── Visualization.png (视觉化图片)\n"
                       "      │   └── Affirmation/ (肯定语)\n"
                       "      │       ├── *.wav (肯定语音频)\n"
                       "      │       └── Raw.txt (肯定语文本)\n"
                       "      └── Releases/ (发行版)\n"
                       "          ├── Audio/ (音频输出)\n"
                       "          └── Video/ (视频输出)")
            )

        logger.info("UI文本重新翻译完成")

    def preview_zoom_in(self):
        """放大预览视图"""
        if not hasattr(self, 'preview_zoom_level'):
            self.preview_zoom_level = 1.0

        self.preview_zoom_level = min(self.preview_zoom_level * 1.2, 3.0)
        self._apply_preview_zoom()
        logger.debug(f"预览放大到: {self.preview_zoom_level:.0%}")

    def preview_zoom_out(self):
        """缩小预览视图"""
        if not hasattr(self, 'preview_zoom_level'):
            self.preview_zoom_level = 1.0

        self.preview_zoom_level = max(self.preview_zoom_level / 1.2, 0.3)
        self._apply_preview_zoom()
        logger.debug(f"预览缩小到: {self.preview_zoom_level:.0%}")

    def preview_reset(self):
        """重置预览视图"""
        self.preview_zoom_level = 1.0
        self._apply_preview_zoom()

        # 重置滚动位置
        if hasattr(self, 'preview_scroll'):
            self.preview_scroll.horizontalScrollBar().setValue(0)
            self.preview_scroll.verticalScrollBar().setValue(0)

        logger.debug("预览视图已重置")

    def _apply_preview_zoom(self):
        """应用预览缩放"""
        if hasattr(self, 'preview_widget') and hasattr(self, 'preview_zoom_level'):
            # 更新缩放比例显示
            if hasattr(self, 'preview_zoom_label'):
                self.preview_zoom_label.setText(self.tr(f"缩放: {self.preview_zoom_level:.0%}"))

            # 重新生成预览以应用缩放
            self.update_preview()

            # 调整预览区域的尺寸
            base_width = 800
            base_height = 300
            new_width = max(int(base_width * self.preview_zoom_level), 400)
            new_height = max(int(base_height * self.preview_zoom_level), 200)
            
            # 重新计算尺寸并更新
            if hasattr(self, 'preview_widget'):
                self.preview_widget.adjustSize()

    def update_preview(self):
        """更新预览视图"""
        logger.debug("开始更新预览")

        # 清除现有内容
        if hasattr(self, 'preview_layout'):
            # 清除除标签外的所有内容
            while self.preview_layout.count() > 1:
                item = self.preview_layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()

        # 检查是否有音频文件
        affirmation_file = self.affirmation_file.text() if hasattr(self, 'affirmation_file') else ""
        background_file = self.background_file.text() if hasattr(self, 'background_file') else ""

        if not affirmation_file and not background_file:
            self.preview_tracks_label.setText(self.tr("请先选择音频文件"))
            return

        try:
            # 收集所有轨道信息
            tracks = []
            max_duration = 0

            # 背景音乐轨道
            if background_file and os.path.exists(background_file):
                duration = self._get_audio_duration(background_file)
                max_duration = max(max_duration, duration)
                tracks.append({
                    'name': self.tr("背景音乐"),
                    'file': background_file,
                    'color': "#4CAF50",
                    'volume': hasattr(self, 'background_volume') and self.background_volume.value() or 0,
                    'duration': duration,
                    'overlay_index': 0
                })

            # 肯定语轨道
            if affirmation_file and os.path.exists(affirmation_file):
                duration = self._get_audio_duration(affirmation_file)
                tracks.append({
                    'name': self.tr("肯定语"),
                    'file': affirmation_file,
                    'color': "#2196F3",
                    'volume': hasattr(self, 'affirmation_volume') and self.affirmation_volume.value() or 0,
                    'duration': duration,
                    'overlay_index': 0
                })

                # 叠加轨道
                overlay_times = hasattr(self, 'overlay_times') and self.overlay_times.value() or 1
                if overlay_times > 1:
                    for i in range(1, overlay_times):
                        tracks.append({
                            'name': self.tr(f"肯定语 (叠加 {i+1})"),
                            'file': affirmation_file,
                            'color': "#9C27B0",
                            'volume': hasattr(self, 'affirmation_volume') and self.affirmation_volume.value() or 0,
                            'duration': duration,
                            'overlay_index': i
                        })

            # 特定频率音轨
            if hasattr(self, 'freq_track_enabled') and self.freq_track_enabled.isChecked():
                freq = self.freq_track_freq.text() if hasattr(self, 'freq_track_freq') else ""
                if freq:
                    tracks.append({
                        'name': self.tr(f"特定频率 ({freq}Hz)"),
                        'file': None,
                        'color': "#FF9800",
                        'volume': hasattr(self, 'freq_track_volume') and self.freq_track_volume.value() or -200,
                        'duration': max_duration if max_duration > 0 else 60,
                        'overlay_index': 0,
                        'is_freq': True
                    })

            if not tracks:
                self.preview_tracks_label.setText(self.tr("没有可显示的轨道"))
                return

            # 创建带标尺的预览区域
            preview_area = self._create_preview_with_rulers(tracks, max_duration if max_duration > 0 else 60)
            self.preview_layout.addWidget(preview_area)

            # 更新标签
            self.preview_tracks_label.setText(self.tr(f"轨道预览 - 共 {len(tracks)} 个轨道"))

            logger.info(f"预览更新完成，共 {len(tracks)} 个轨道")

        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            self.preview_tracks_label.setText(self.tr(f"预览更新失败: {str(e)}"))

    def _get_audio_duration(self, file_path):
        """获取音频文件时长（秒）

        Args:
            file_path: 音频文件路径

        Returns:
            float: 音频时长（秒），失败返回0
        """
        if not file_path or not os.path.exists(file_path):
            return 0

        ext = os.path.splitext(file_path)[1].lower()

        # 1. 尝试使用 wave 模块读取 WAV 文件（标准库，无需额外依赖）
        if ext == '.wav':
            try:
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    if rate > 0:
                        return frames / float(rate)
            except Exception as e:
                logger.debug(f"使用 wave 模块读取失败: {e}")

        # 2. 尝试使用 mutagen 读取各种音频格式（轻量级，推荐）
        try:
            from mutagen import File
            audio = File(file_path)
            if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                return audio.info.length
        except ImportError:
            logger.debug("mutagen 未安装，跳过")
        except Exception as e:
            logger.debug(f"使用 mutagen 读取失败: {e}")

        # 3. 尝试使用 soundfile 读取各种音频格式
        try:
            import soundfile as sf
            info = sf.info(file_path)
            return info.duration
        except ImportError:
            logger.debug("soundfile 未安装，跳过")
        except Exception as e:
            logger.debug(f"使用 soundfile 读取失败: {e}")

        # 4. 尝试使用 audioread 读取各种音频格式
        try:
            import audioread
            with audioread.audio_open(file_path) as f:
                return f.duration
        except ImportError:
            logger.debug("audioread 未安装，跳过")
        except Exception as e:
            logger.debug(f"使用 audioread 读取失败: {e}")

        # 5. 尝试使用 pydub（如果可用）
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0
        except ImportError:
            logger.debug("pydub 未安装，跳过")
        except Exception as e:
            logger.debug(f"使用 pydub 读取失败: {e}")

        # 6. 尝试使用 ffprobe（如果系统已安装 ffmpeg）
        if self.ffmpeg_available:
            try:
                import subprocess
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    duration = float(result.stdout.strip())
                    if duration > 0:
                        return duration
            except Exception as e:
                logger.debug(f"使用 ffprobe 读取失败: {e}")

        # 如果都失败了，返回默认值
        logger.warning(f"无法获取音频时长: {file_path}，请安装 mutagen、soundfile、audioread 或 pydub 以支持更多格式")
        return 0

    def _create_track_widget(self, name, file_path, color, volume, overlay_index=0):
        """创建轨道显示组件

        Args:
            name: 轨道名称
            file_path: 音频文件路径
            color: 轨道颜色
            volume: 音量值
            overlay_index: 叠加索引（0表示主轨道）

        Returns:
            QWidget: 轨道组件
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 2, 5, 2)

        # 轨道名称
        name_label = QLabel(name)
        name_label.setFixedWidth(120)
        name_label.setStyleSheet(f"font-weight: bold; color: {color};")
        layout.addWidget(name_label)

        # 音频波形/时长显示
        duration_sec = self._get_audio_duration(file_path)

        if duration_sec > 0:
            # 时长标签
            duration_label = QLabel(f"{duration_sec:.1f}s")
            duration_label.setFixedWidth(60)
            layout.addWidget(duration_label)

            # 音量标签（volume 是实际 dB 值的 10 倍，需要除以 10）
            vol_label = QLabel(f"{volume/10:.1f}dB")
            vol_label.setFixedWidth(50)
            layout.addWidget(vol_label)

            # 波形可视化（简化版 - 使用彩色条表示）
            waveform_widget = QWidget()
            waveform_layout = QHBoxLayout(waveform_widget)
            waveform_layout.setSpacing(1)
            waveform_layout.setContentsMargins(0, 0, 0, 0)

            # 创建简化的波形条
            num_bars = min(50, max(10, int(duration_sec)))
            for i in range(num_bars):
                bar = QWidget()
                bar.setFixedWidth(8)
                # 随机高度模拟波形
                import random
                height = random.randint(20, 60)
                bar.setFixedHeight(height)
                bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
                waveform_layout.addWidget(bar)

            waveform_layout.addStretch()
            layout.addWidget(waveform_widget, 1)

            # 叠加延迟信息
            if overlay_index > 0:
                interval = hasattr(self, 'overlay_interval') and self.overlay_interval.value() or 0
                delay_ms = overlay_index * interval
                delay_label = QLabel(f"+{delay_ms}ms")
                delay_label.setStyleSheet("color: #666; font-size: 10px;")
                delay_label.setFixedWidth(60)
                layout.addWidget(delay_label)
        else:
            error_label = QLabel(self.tr("无法加载音频信息"))
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label, 1)

        # 设置轨道样式
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {color}15;
                border: 1px solid {color};
                border-radius: 4px;
            }}
        """)

        return widget

    def _create_freq_track_widget(self, freq):
        """创建特定频率轨道显示组件

        Args:
            freq: 频率值(Hz)

        Returns:
            QWidget: 频率轨道组件
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 2, 5, 2)

        color = "#FF9800"

        # 轨道名称
        name_label = QLabel(self.tr(f"特定频率 ({freq}Hz)"))
        name_label.setFixedWidth(120)
        name_label.setStyleSheet(f"font-weight: bold; color: {color};")
        layout.addWidget(name_label)

        # 频率可视化
        freq_label = QLabel("∞")
        freq_label.setFixedWidth(60)
        layout.addWidget(freq_label)

        # 音量（volume 是实际 dB 值的 10 倍，需要除以 10）
        volume = hasattr(self, 'freq_track_volume') and self.freq_track_volume.value() or -200
        vol_label = QLabel(f"{volume/10:.1f}dB")
        vol_label.setFixedWidth(50)
        layout.addWidget(vol_label)

        # 正弦波可视化
        waveform_widget = QWidget()
        waveform_layout = QHBoxLayout(waveform_widget)
        waveform_layout.setSpacing(2)
        waveform_layout.setContentsMargins(0, 0, 0, 0)

        # 创建正弦波形
        import math
        num_points = 50
        for i in range(num_points):
            bar = QWidget()
            bar.setFixedWidth(6)
            # 正弦波高度
            angle = (i / num_points) * 2 * math.pi * 3  # 3个周期
            height = int(30 + 25 * math.sin(angle))
            bar.setFixedHeight(height)
            bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
            waveform_layout.addWidget(bar)

        waveform_layout.addStretch()
        layout.addWidget(waveform_widget, 1)

        # 设置轨道样式
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {color}15;
                border: 1px solid {color};
                border-radius: 4px;
            }}
        """)

        return widget

    def _create_preview_with_rulers(self, tracks, max_duration):
        """创建带标尺的预览区域

        Args:
            tracks: 轨道信息列表
            max_duration: 最大时长（秒）

        Returns:
            QWidget: 预览区域组件
        """
        # 主容器
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部：时间标尺
        time_ruler = self._create_time_ruler(max_duration)
        main_layout.addWidget(time_ruler)

        # 中间：轨道区域和音量标尺
        middle_area = QWidget()
        middle_layout = QHBoxLayout(middle_area)
        middle_layout.setSpacing(0)
        middle_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧：轨道列表
        tracks_widget = QWidget()
        tracks_layout = QVBoxLayout(tracks_widget)
        tracks_layout.setSpacing(5)
        tracks_layout.setContentsMargins(5, 5, 5, 5)

        # 计算每个轨道的宽度（基于时间比例和缩放级别）
        zoom_level = getattr(self, 'preview_zoom_level', 1.0)
        pixels_per_second = int(20 * zoom_level)  # 基础每秒20像素，应用缩放
        total_width = max(int(max_duration * pixels_per_second), 400)

        for track in tracks:
            track_widget = self._create_timeline_track(track, total_width, max_duration)
            tracks_layout.addWidget(track_widget)

        tracks_layout.addStretch()
        middle_layout.addWidget(tracks_widget, 1)

        main_layout.addWidget(middle_area, 1)

        return container

    def _create_time_ruler(self, max_duration):
        """创建时间标尺

        Args:
            max_duration: 最大时长（秒）

        Returns:
            QWidget: 时间标尺组件
        """
        ruler = QWidget()
        ruler.setFixedHeight(30)
        ruler.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ccc;")

        layout = QHBoxLayout(ruler)
        layout.setSpacing(0)
        layout.setContentsMargins(5, 0, 5, 0)

        # 左侧留白（与轨道名称对齐）
        spacer = QWidget()
        spacer.setFixedWidth(120)
        layout.addWidget(spacer)

        # 时间刻度区域
        scale_widget = QWidget()
        scale_layout = QHBoxLayout(scale_widget)
        scale_layout.setSpacing(0)
        scale_layout.setContentsMargins(0, 0, 0, 0)

        # 使用缩放级别
        zoom_level = getattr(self, 'preview_zoom_level', 1.0)
        pixels_per_second = int(20 * zoom_level)
        total_width = max(int(max_duration * pixels_per_second), 400)

        # 计算刻度间隔（根据缩放级别和时长动态调整）
        if max_duration <= 10:
            interval = 1  # 1秒
        elif max_duration <= 30:
            interval = 5 if zoom_level >= 1.0 else 10  # 根据缩放调整
        elif max_duration <= 60:
            interval = 10 if zoom_level >= 0.8 else 20
        elif max_duration <= 300:
            interval = 30 if zoom_level >= 0.5 else 60
        else:
            interval = 60 if zoom_level >= 0.3 else 120

        # 添加时间刻度
        for t in range(0, int(max_duration) + 1, interval):
            tick = QLabel(f"{t}s")
            tick.setStyleSheet("font-size: 10px; color: #666;")
            tick.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            tick.setFixedWidth(int(interval * pixels_per_second))
            scale_layout.addWidget(tick)

        scale_layout.addStretch()
        layout.addWidget(scale_widget, 1)

        # 右侧留白（与音量指示对齐）
        spacer2 = QWidget()
        spacer2.setFixedWidth(60)
        layout.addWidget(spacer2)

        return ruler

    def _create_volume_ruler(self):
        """创建音量标尺

        Returns:
            QWidget: 音量标尺组件
        """
        ruler = QWidget()
        ruler.setFixedWidth(40)
        ruler.setStyleSheet("background-color: #f8f8f8; border-left: 1px solid #ccc;")

        layout = QVBoxLayout(ruler)
        layout.setSpacing(0)
        layout.setContentsMargins(2, 5, 2, 5)

        # 音量刻度（从0dB到-60dB）
        volumes = [0, -10, -20, -30, -40, -50, -60]
        for vol in volumes:
            label = QLabel(f"{vol}")
            label.setStyleSheet("font-size: 9px; color: #666;")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(label)

        layout.addStretch()
        return ruler

    def _create_timeline_track(self, track, total_width, max_duration):
        """创建时间线轨道

        Args:
            track: 轨道信息字典
            total_width: 总宽度（像素）
            max_duration: 最大时长（秒）

        Returns:
            QWidget: 轨道组件
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 2, 5, 2)

        color = track['color']
        name = track['name']
        duration = track.get('duration', 0)
        volume = track.get('volume', 0)
        overlay_index = track.get('overlay_index', 0)

        # 轨道名称
        name_label = QLabel(name)
        name_label.setFixedWidth(120)
        name_label.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 11px;")
        name_label.setToolTip(f"{name}\n时长: {duration:.1f}s\n音量: {volume/10:.1f}dB")
        layout.addWidget(name_label)

        # 时间线区域
        timeline_widget = QWidget()
        timeline_widget.setFixedWidth(total_width)
        timeline_widget.setMinimumHeight(40)
        timeline_widget.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")

        timeline_layout = QHBoxLayout(timeline_widget)
        timeline_layout.setSpacing(0)
        timeline_layout.setContentsMargins(0, 0, 0, 0)

        if duration > 0:
            # 使用与预览区域相同的缩放级别
            zoom_level = getattr(self, 'preview_zoom_level', 1.0)
            pixels_per_second = int(20 * zoom_level)

            # 叠加延迟
            if overlay_index > 0:
                interval = hasattr(self, 'overlay_interval') and self.overlay_interval.value() or 0
                delay_ms = overlay_index * interval
                delay_sec = delay_ms / 1000.0
                delay_width = int(delay_sec * pixels_per_second)

                if delay_width > 0:
                    delay_spacer = QWidget()
                    delay_spacer.setFixedWidth(delay_width)
                    delay_spacer.setStyleSheet("background-color: transparent;")
                    timeline_layout.addWidget(delay_spacer)

            # 音频块
            audio_width = int(duration * pixels_per_second)
            audio_block = QWidget()
            audio_block.setFixedWidth(audio_width)
            audio_block.setMinimumHeight(36)

            # 根据音量设置透明度
            vol_db = volume / 10.0
            opacity = max(0.3, min(1.0, 1.0 + (vol_db / 60.0)))  # -60dB = 0.3, 0dB = 1.0

            audio_block.setStyleSheet(f"""
                QWidget {{
                    background-color: {color};
                    border-radius: 3px;
                    opacity: {opacity};
                }}
            """)

            # 添加波形效果
            waveform_layout = QHBoxLayout(audio_block)
            waveform_layout.setSpacing(1)
            waveform_layout.setContentsMargins(3, 3, 3, 3)

            num_bars = max(5, min(30, int(duration)))
            import random
            for i in range(num_bars):
                bar = QWidget()
                bar.setFixedWidth(max(2, audio_width // num_bars - 1))
                height = random.randint(10, 30)
                bar.setFixedHeight(height)
                bar.setStyleSheet(f"background-color: rgba(255,255,255,0.5); border-radius: 1px;")
                waveform_layout.addWidget(bar)

            waveform_layout.addStretch()
            timeline_layout.addWidget(audio_block)

        timeline_layout.addStretch()
        layout.addWidget(timeline_widget)

        # 轨道独立音量指示
        volume_widget = QWidget()
        volume_widget.setFixedWidth(60)
        volume_layout = QVBoxLayout(volume_widget)
        volume_layout.setSpacing(0)
        volume_layout.setContentsMargins(5, 2, 5, 2)

        # 音量值显示
        vol_label = QLabel(f"{volume/10:.1f}dB")
        vol_label.setStyleSheet(f"font-size: 10px; color: {color}; font-weight: bold;")
        vol_label.setAlignment(Qt.AlignCenter)
        volume_layout.addWidget(vol_label)

        # 音量条
        vol_bar_widget = QWidget()
        vol_bar_widget.setFixedSize(40, 20)
        vol_bar_layout = QHBoxLayout(vol_bar_widget)
        vol_bar_layout.setSpacing(1)
        vol_bar_layout.setContentsMargins(1, 1, 1, 1)

        # 计算音量条长度（0-60dB 对应 0-40像素）
        vol_percent = 1.0 - (abs(volume) / 600.0)  # volume 是 10倍的 dB 值
        vol_bar_width = max(5, int(40 * vol_percent))

        vol_bar = QWidget()
        vol_bar.setFixedSize(vol_bar_width, 18)
        vol_bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        vol_bar_layout.addWidget(vol_bar)
        vol_bar_layout.addStretch()

        volume_layout.addWidget(vol_bar_widget)
        volume_layout.addStretch()
        layout.addWidget(volume_widget)

        # 设置轨道样式
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {color}08;
                border-radius: 4px;
            }}
        """)

        return widget

    def enumerate_tts_engines(self):
        """枚举系统中已安装的TTS引擎"""
        logger.debug("开始枚举TTS引擎")
        
        try:
            # 清空现有选项
            self.tts_engine.clear()
            
            # 添加默认选项
            self.tts_engine.addItem(self.tr("系统默认"))
            
            # 使用pyttsx3枚举TTS引擎
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            logger.debug(f"找到 {len(voices)} 个TTS语音")
            
            for voice in voices:
                # 获取引擎名称，通常包含在voice.id中
                voice_name = voice.name
                if hasattr(voice, 'id'):
                    # 从ID中提取引擎信息
                    if 'microsoft' in voice.id.lower():
                        engine_name = f"Microsoft - {voice_name}"
                    elif 'google' in voice.id.lower():
                        engine_name = f"Google - {voice_name}"
                    else:
                        engine_name = voice_name
                    
                    self.tts_engine.addItem(engine_name)
                    logger.debug(f"添加TTS引擎: {engine_name}")
            
            # 释放引擎资源
            engine.stop()
            logger.info(f"TTS引擎枚举完成，共找到 {len(voices)} 个语音")
            
        except Exception as e:
            # 如果枚举失败，保留默认选项
            logger.error(f"TTS引擎枚举失败: {e}")
            self.tts_engine.clear()
            self.tts_engine.addItem(self.tr("系统默认"))
            self.tts_engine.addItem("Microsoft")
            self.tts_engine.addItem("Google")
            logger.warning("使用默认TTS引擎选项")
    
    def enumerate_audio_devices(self):
        """枚举系统中可用的音频输入设备"""
        logger.debug("开始枚举音频输入设备")

        try:
            # 清空现有选项
            self.record_device.clear()

            # 添加默认选项
            self.record_device.addItem(self.tr("系统默认"))

            # 使用pyaudio枚举音频设备
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            logger.debug(f"系统中共有 {device_count} 个音频设备")

            input_devices = []
            seen_names = set()  # 用于去重

            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)

                # 只显示输入设备（麦克风）
                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name']
                    # 清理设备名称中的特殊字符
                    device_name = device_name.strip()

                    # 跳过重复设备
                    if device_name in seen_names:
                        logger.debug(f"跳过重复设备: {device_name}")
                        continue

                    # 过滤掉虚拟设备和监控设备
                    skip_keywords = ['monitor', 'loopback', 'null', 'dummy', 'pulseaudio',
                                     'default', 'hw:', 'surround', 'hdmi', 'spdif', 'sysdefault',
                                     'front:', 'rear:', 'center_lfe:', 'side:', 'iec958',
                                     'dmix', 'dsnoop', 'plughw', 'usbstream', 'jack',
                                     'alsa', 'oss', 'a52', 'vdownmix', 'upmix', 'Chromium',
                                     'Firefox', 'lavrate', 'samplerate', 'speexrate',
                                     'pulse', 'speex', 'pipewire']
                    if any(keyword in device_name.lower() for keyword in skip_keywords):
                        logger.debug(f"过滤掉虚拟/监控设备: {device_name}")
                        continue

                    seen_names.add(device_name)

                    # 添加设备到下拉列表，同时存储设备索引
                    self.record_device.addItem(device_name, i)
                    input_devices.append((device_name, i))
                    logger.debug(f"添加音频输入设备: {device_name} (索引: {i})")

            # 释放pyaudio资源
            p.terminate()
            logger.info(f"音频设备枚举完成，共找到 {len(input_devices)} 个输入设备")

        except Exception as e:
            # 如果枚举失败，保留默认选项
            logger.error(f"音频设备枚举失败: {e}")
            self.record_device.clear()
            self.record_device.addItem(self.tr("系统默认"))
            self.record_device.addItem(self.tr("麦克风 (Realtek)"))
            logger.warning("使用默认音频设备选项")
    
    def get_affirmation_output_dir(self):
        """获取肯定语输出目录"""
        project_dir = self.get_current_project_dir()
        if project_dir:
            return os.path.join(project_dir, "Assets", "Affirmation")
        return None

    def check_project_selected(self):
        """检查是否选择了项目"""
        if not hasattr(self, 'current_project_name') or not self.current_project_name:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请先选择一个项目！"))
            return False
        return True

    def generate_tts_audio(self):
        """使用TTS引擎生成肯定语音频"""
        logger.info("开始生成TTS音频")

        # 检查是否选择了项目
        if not self.check_project_selected():
            return

        try:
            # 检查是否有文本输入
            if not self.affirmation_text.text().strip():
                logger.warning("未输入肯定语文本")
                QMessageBox.warning(self, self.tr("警告"),
                                   self.tr("请输入肯定语文本！"))
                return

            # 获取输出文件路径
            output_dir = self.get_affirmation_output_dir()
            if not output_dir:
                QMessageBox.warning(self, self.tr("错误"),
                                   self.tr("无法获取项目目录！"))
                return

            import os
            if not os.path.exists(output_dir):
                logger.debug(f"创建输出目录: {output_dir}")
                os.makedirs(output_dir)
            
            # 生成文件名（基于文本内容）
            import hashlib
            text_hash = hashlib.md5(self.affirmation_text.text().strip().encode()).hexdigest()[:8]
            output_file = os.path.join(output_dir, f"tts_generated_{text_hash}.wav")
            logger.debug(f"生成输出文件路径: {output_file}")
            
            # 获取选中的TTS引擎
            selected_engine = self.tts_engine.currentText()
            logger.debug(f"选中的TTS引擎: {selected_engine}")
            
            # 初始化TTS引擎
            engine = pyttsx3.init()
            
            # 设置语音属性
            voices = engine.getProperty('voices')
            logger.debug(f"可用的语音数量: {len(voices)}")
            
            # 如果选择了特定引擎，尝试设置对应的语音
            if selected_engine != self.tr("系统默认"):
                logger.debug("尝试设置特定语音引擎")
                for voice in voices:
                    voice_name = voice.name
                    if hasattr(voice, 'id'):
                        # 构建引擎名称进行匹配
                        if 'microsoft' in voice.id.lower() and 'microsoft' in selected_engine.lower():
                            if voice_name in selected_engine:
                                engine.setProperty('voice', voice.id)
                                logger.debug(f"设置Microsoft语音: {voice_name}")
                                break
                        elif 'google' in voice.id.lower() and 'google' in selected_engine.lower():
                            if voice_name in selected_engine:
                                engine.setProperty('voice', voice.id)
                                logger.debug(f"设置Google语音: {voice_name}")
                                break
            else:
                logger.debug("使用系统默认语音引擎")
            
            # 设置语速（可选）
            engine.setProperty('rate', 150)  # 默认语速
            logger.debug("设置语速: 150")
            
            # 设置音量（可选）
            engine.setProperty('volume', 0.8)  # 默认音量
            logger.debug("设置音量: 0.8")
            
            # 保存音频到文件
            logger.debug("开始生成音频文件")
            engine.save_to_file(self.affirmation_text.text().strip(), output_file)
            engine.runAndWait()
            
            # 更新音频文件路径
            self.affirmation_file.setText(output_file)
            
            logger.info(f"TTS音频生成成功: {output_file}")
            QMessageBox.information(self, self.tr("成功"), 
                                   self.tr(f"TTS音频生成成功！文件已保存到: {output_file}"))
            
        except Exception as e:
            logger.error(f"TTS音频生成失败: {e}")
            QMessageBox.critical(self, self.tr("错误"), 
                               self.tr(f"TTS音频生成失败: {str(e)}"))
        
    def initUI(self):
        self.setWindowTitle(self.tr("SMake"))
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央widget和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        
        # 创建滚动区域（适应不同屏幕大小）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 创建选项卡内容
        project_widget = QWidget()
        project_layout = QVBoxLayout(project_widget)
        project_layout.addWidget(self.create_project_group())

        affirmation_widget = QWidget()
        affirmation_layout = QVBoxLayout(affirmation_widget)
        affirmation_layout.addWidget(self.create_affirmation_group())

        background_widget = QWidget()
        background_layout = QVBoxLayout(background_widget)
        background_layout.addWidget(self.create_background_group())

        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.addWidget(self.create_output_group())

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.addWidget(self.create_settings_group())

        # 创建特定频率音轨选项卡内容
        freq_track_widget = QWidget()
        freq_track_layout = QVBoxLayout(freq_track_widget)
        freq_track_layout.addWidget(self.create_freq_track_group())

        # 创建日志选项卡内容
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.addWidget(self.create_log_group())

        # 添加选项卡
        self.project_tab_index = self.tab_widget.addTab(project_widget, self.tr("项目"))
        self.affirmation_tab_index = self.tab_widget.addTab(affirmation_widget, self.tr("肯定语"))
        self.background_tab_index = self.tab_widget.addTab(background_widget, self.tr("背景音"))
        self.freq_track_tab_index = self.tab_widget.addTab(freq_track_widget, self.tr("特定频率音轨"))
        self.output_tab_index = self.tab_widget.addTab(output_widget, self.tr("输出"))
        self.settings_tab_index = self.tab_widget.addTab(settings_widget, self.tr("设置"))
        self.log_tab_index = self.tab_widget.addTab(log_widget, self.tr("日志"))

        main_layout.addWidget(self.tab_widget)

        # 根据ffmpeg可用性更新UI
        self.update_ui_for_ffmpeg_availability()
        
    def create_project_group(self):
        """创建项目组"""
        self.project_group = QGroupBox(self.tr("项目管理"))
        layout = QGridLayout()

        # 当前项目组显示
        self.label_current_project_group = QLabel(self.tr("当前项目组:"))
        layout.addWidget(self.label_current_project_group, 0, 0)
        self.current_project_group_label = QLabel(self.tr("默认项目组"))
        self.current_project_group_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        layout.addWidget(self.current_project_group_label, 0, 1, 1, 2)

        # 项目组列表
        self.label_project_group_list = QLabel(self.tr("项目组列表:"))
        layout.addWidget(self.label_project_group_list, 1, 0)
        self.project_group_list = QComboBox()
        self.project_group_list.setToolTip(self.tr("选择或切换当前项目组"))
        self.project_group_list.currentIndexChanged.connect(self.on_project_group_selected)
        layout.addWidget(self.project_group_list, 1, 1, 1, 2)

        # 新建项目组
        self.label_new_project_group = QLabel(self.tr("新建项目组:"))
        layout.addWidget(self.label_new_project_group, 2, 0)
        self.new_project_group_name = QLineEdit()
        self.new_project_group_name.setToolTip(self.tr("输入新项目组名称"))
        self.new_project_group_name.setPlaceholderText(self.tr("输入项目组名称"))
        layout.addWidget(self.new_project_group_name, 2, 1)

        self.create_project_group_btn = QPushButton(self.tr("创建项目组"))
        self.create_project_group_btn.setToolTip(self.tr("创建新项目组"))
        self.create_project_group_btn.clicked.connect(self.create_new_project_group)
        layout.addWidget(self.create_project_group_btn, 2, 2)

        # 删除项目组按钮
        self.delete_project_group_btn = QPushButton(self.tr("删除项目组"))
        self.delete_project_group_btn.setToolTip(self.tr("删除选中的项目组"))
        self.delete_project_group_btn.clicked.connect(self.delete_project_group)
        layout.addWidget(self.delete_project_group_btn, 3, 0, 1, 3)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #ccc;")
        layout.addWidget(line, 4, 0, 1, 3)

        # 当前项目显示
        self.label_current_project = QLabel(self.tr("当前项目:"))
        layout.addWidget(self.label_current_project, 5, 0)
        self.current_project_label = QLabel(self.tr("未选择项目"))
        self.current_project_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addWidget(self.current_project_label, 5, 1, 1, 2)

        # 项目列表
        self.label_project_list = QLabel(self.tr("项目列表:"))
        layout.addWidget(self.label_project_list, 6, 0)
        self.project_list = QComboBox()
        self.project_list.setToolTip(self.tr("选择或切换当前项目"))
        self.project_list.currentIndexChanged.connect(self.on_project_selected)
        layout.addWidget(self.project_list, 6, 1, 1, 2)

        # 刷新项目列表按钮
        self.refresh_projects_btn = QPushButton(self.tr("刷新"))
        self.refresh_projects_btn.setToolTip(self.tr("刷新项目列表"))
        self.refresh_projects_btn.clicked.connect(self.refresh_project_list)
        layout.addWidget(self.refresh_projects_btn, 7, 0)

        # 新建项目
        self.label_new_project = QLabel(self.tr("新建项目:"))
        layout.addWidget(self.label_new_project, 8, 0)
        self.new_project_name = QLineEdit()
        self.new_project_name.setToolTip(self.tr("输入新项目名称"))
        self.new_project_name.setPlaceholderText(self.tr("输入项目名称"))
        layout.addWidget(self.new_project_name, 8, 1)

        self.create_project_btn = QPushButton(self.tr("创建项目"))
        self.create_project_btn.setToolTip(self.tr("创建新项目"))
        self.create_project_btn.clicked.connect(self.create_project)
        layout.addWidget(self.create_project_btn, 8, 2)

        # 删除项目按钮
        self.delete_project_btn = QPushButton(self.tr("删除项目"))
        self.delete_project_btn.setToolTip(self.tr("删除选中的项目"))
        self.delete_project_btn.clicked.connect(self.delete_project)
        layout.addWidget(self.delete_project_btn, 9, 0, 1, 3)

        # 项目路径信息
        self.label_project_path = QLabel(self.tr("项目路径:"))
        layout.addWidget(self.label_project_path, 10, 0)
        self.project_path_label = QLabel("./Project/")
        self.project_path_label.setStyleSheet("color: gray;")
        self.project_path_label.setWordWrap(True)
        layout.addWidget(self.project_path_label, 10, 1, 1, 2)

        # 分隔线 - 导入导出区域
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: #ccc;")
        layout.addWidget(line2, 11, 0, 1, 3)

        # 导入导出按钮
        self.label_import_export = QLabel(self.tr("导入/导出:"))
        layout.addWidget(self.label_import_export, 12, 0)

        self.export_project_btn = QPushButton(self.tr("导出项目"))
        self.export_project_btn.setToolTip(self.tr("将当前项目导出为压缩文件"))
        self.export_project_btn.clicked.connect(self.export_project)
        layout.addWidget(self.export_project_btn, 12, 1)

        self.export_project_group_btn = QPushButton(self.tr("导出项目组"))
        self.export_project_group_btn.setToolTip(self.tr("将当前项目组导出为压缩文件"))
        self.export_project_group_btn.clicked.connect(self.export_project_group)
        layout.addWidget(self.export_project_group_btn, 12, 2)

        self.import_btn = QPushButton(self.tr("导入"))
        self.import_btn.setToolTip(self.tr("从压缩文件导入项目或项目组"))
        self.import_btn.clicked.connect(self.import_project_or_group)
        layout.addWidget(self.import_btn, 13, 0, 1, 3)

        # 项目结构说明
        self.project_structure_group = QGroupBox(self.tr("项目结构"))
        structure_layout = QVBoxLayout()
        self.project_structure_label = QLabel(
            self.tr("项目组名称/\n"
                   "  └── 项目名称/\n"
                   "      ├── README.md (项目描述)\n"
                   "      ├── config.json (项目配置)\n"
                   "      ├── Assets/ (资产)\n"
                   "      │   ├── BGM.wav (背景音乐)\n"
                   "      │   ├── Visualization.png (视觉化图片)\n"
                   "      │   └── Affirmation/ (肯定语)\n"
                   "      │       ├── *.wav (肯定语音频)\n"
                   "      │       └── Raw.txt (肯定语文本)\n"
                   "      └── Releases/ (发行版)\n"
                   "          ├── Audio/ (音频输出)\n"
                   "          └── Video/ (视频输出)")
        )
        self.project_structure_label.setStyleSheet("font-family: monospace; color: #666;")
        structure_layout.addWidget(self.project_structure_label)
        self.project_structure_group.setLayout(structure_layout)
        layout.addWidget(self.project_structure_group, 14, 0, 1, 3)

        self.project_group.setLayout(layout)

        # 初始化时刷新项目组列表
        self.refresh_project_group_list()

        return self.project_group

    def create_affirmation_group(self):
        """创建肯定语组"""
        self.affirmation_group = QGroupBox(self.tr("肯定语"))
        layout = QGridLayout()

        # 文件选择
        self.label_audio_file = QLabel(self.tr("音频文件:"))
        layout.addWidget(self.label_audio_file, 0, 0)
        self.affirmation_file = QLineEdit()
        self.affirmation_file.setToolTip(self.tr("选择一个音频文件作为肯定语。"))
        layout.addWidget(self.affirmation_file, 0, 1)

        self.btn_browse_aff = QPushButton(self.tr("浏览..."))
        self.btn_browse_aff.clicked.connect(lambda: self.browse_file(self.affirmation_file,
                                                              self.tr("音频文件 (*.mp3 *.wav)")))
        self.btn_browse_aff.setToolTip(self.tr("选择音频文件"))
        layout.addWidget(self.btn_browse_aff, 0, 2)

        # 肯定语文本输入
        self.label_affirmation_text = QLabel(self.tr("肯定语:"))
        layout.addWidget(self.label_affirmation_text, 1, 0)
        self.affirmation_text = QLineEdit()
        self.affirmation_text.setToolTip(self.tr("输入肯定语。"))
        layout.addWidget(self.affirmation_text, 1, 1, 1, 2)

        # 文本文件选择
        self.label_text_file = QLabel(self.tr("文本文件:"))
        layout.addWidget(self.label_text_file, 2, 0)
        self.text_file = QLineEdit()
        self.text_file.setToolTip(self.tr("选择一个文本文件作为肯定语。"))
        layout.addWidget(self.text_file, 2, 1)

        self.btn_browse_text = QPushButton(self.tr("浏览..."))
        self.btn_browse_text.clicked.connect(lambda: self.browse_file(self.text_file,
                                                               self.tr("文本文件 (*.txt)")))
        self.btn_browse_text.setToolTip(self.tr("选择文本文件"))
        layout.addWidget(self.btn_browse_text, 2, 2)

        # TTS引擎选择
        self.label_tts_engine = QLabel(self.tr("TTS引擎:"))
        layout.addWidget(self.label_tts_engine, 3, 0)
        self.tts_engine = QComboBox()
        self.tts_engine.setToolTip(self.tr("选择从文本生成肯定语音频时要使用的TTS引擎。"))
        layout.addWidget(self.tts_engine, 3, 1)

        # 生成按钮
        self.generate_tts_btn = QPushButton(self.tr("生成"))
        self.generate_tts_btn.setToolTip(self.tr("通过TTS从文本生成肯定语。"))
        self.generate_tts_btn.clicked.connect(self.generate_tts_audio)
        layout.addWidget(self.generate_tts_btn, 3, 2)

        # 录制设备选择
        self.label_record_device = QLabel(self.tr("录制设备:"))
        layout.addWidget(self.label_record_device, 4, 0)
        self.record_device = QComboBox()
        self.record_device.setToolTip(self.tr("选择录制肯定语音频时要使用的设备。"))
        layout.addWidget(self.record_device, 4, 1)

        # 开始/停止录制按钮
        self.record_btn = QPushButton(self.tr("开始录制"))
        self.record_btn.setCheckable(True)
        self.record_btn.setToolTip(self.tr("开始/停止录制肯定语。"))
        self.record_btn.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_btn, 4, 2)

        # 音量滑条
        self.label_volume = QLabel(self.tr("音量:"))
        layout.addWidget(self.label_volume, 5, 0)
        self.affirmation_volume = QSlider(Qt.Horizontal)
        self.affirmation_volume.setRange(-600, 0)  # -60.0 to 0.0 dB (乘以10)
        self.affirmation_volume.setValue(-230)
        self.affirmation_volume.setToolTip(self.tr("改变肯定语音轨的音量。（单位为分贝）"))
        layout.addWidget(self.affirmation_volume, 5, 1)

        self.affirmation_volume_spin = QDoubleSpinBox()
        self.affirmation_volume_spin.setRange(-60.0, 0.0)
        self.affirmation_volume_spin.setValue(-23.0)
        self.affirmation_volume_spin.setSingleStep(0.5)
        self.affirmation_volume_spin.valueChanged.connect(
            lambda v: self.affirmation_volume.setValue(int(v * 10)))
        self.affirmation_volume.valueChanged.connect(
            lambda v: self.affirmation_volume_spin.setValue(v / 10.0))
        layout.addWidget(self.affirmation_volume_spin, 5, 2)

        # 频率选择
        self.label_freq_mode = QLabel(self.tr("频率模式:"))
        layout.addWidget(self.label_freq_mode, 6, 0)
        self.frequency_mode = QComboBox()
        self.frequency_mode.addItems([self.tr("Raw（保持不变）"),
                                     self.tr("UG（亚超声波）"),
                                     self.tr("传统（次声波）")])
        self.frequency_mode.setToolTip(self.tr("改变肯定语音轨的频率，推荐使用地下（UG）模式。"))
        layout.addWidget(self.frequency_mode, 6, 1, 1, 2)

        # 倍速滑条
        self.label_speed = QLabel(self.tr("倍速:"))
        layout.addWidget(self.label_speed, 7, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 100)  # 1.0 to 10.0 (乘以10)
        self.speed_slider.setValue(10)
        self.speed_slider.setToolTip(self.tr("改变肯定语音轨的倍速。"))
        layout.addWidget(self.speed_slider, 7, 1)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(1.0, 10.0)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.valueChanged.connect(
            lambda v: self.speed_slider.setValue(int(v * 10)))
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_spin.setValue(v / 10.0))
        layout.addWidget(self.speed_spin, 7, 2)

        # 倒放复选框
        self.reverse_check = QCheckBox(self.tr("倒放"))
        self.reverse_check.setToolTip(self.tr("肯定语是否倒放。"))
        layout.addWidget(self.reverse_check, 8, 1, 1, 2)

        # 叠加组
        self.overlay_group = QGroupBox(self.tr("叠加设置"))
        overlay_layout = QGridLayout()

        # 叠加次数
        self.label_overlay_times = QLabel(self.tr("叠加次数:"))
        overlay_layout.addWidget(self.label_overlay_times, 0, 0)
        self.overlay_times = QSpinBox()
        self.overlay_times.setRange(1, 10)
        self.overlay_times.setValue(1)
        self.overlay_times.setToolTip(self.tr("肯定语音轨的叠加次数。"))
        overlay_layout.addWidget(self.overlay_times, 0, 1)

        # 叠加间隔
        self.label_overlay_interval = QLabel(self.tr("间隔:"))
        overlay_layout.addWidget(self.label_overlay_interval, 1, 0)
        self.overlay_interval = QDoubleSpinBox()
        self.overlay_interval.setRange(0.0, 10.0)
        self.overlay_interval.setValue(1.0)
        self.overlay_interval.setSingleStep(0.1)
        self.overlay_interval.setToolTip(self.tr("每次叠加后，下一个叠加音轨应比上一个延后多少时间？"))
        overlay_layout.addWidget(self.overlay_interval, 1, 1)

        # 音量递减速率
        self.label_volume_decrease = QLabel(self.tr("音量递减:"))
        overlay_layout.addWidget(self.label_volume_decrease, 2, 0)
        self.volume_decrease = QDoubleSpinBox()
        self.volume_decrease.setRange(0.0, 10.0)
        self.volume_decrease.setValue(0.0)
        self.volume_decrease.setSingleStep(0.5)
        self.volume_decrease.setToolTip(self.tr("每次叠加后，下一个叠加音轨应比上一个音量降低多少？"))
        overlay_layout.addWidget(self.volume_decrease, 2, 1)

        self.overlay_group.setLayout(overlay_layout)
        layout.addWidget(self.overlay_group, 9, 0, 1, 3)

        # 确保肯定语完整性复选框
        self.ensure_integrity_check = QCheckBox(self.tr("确保肯定语完整性"))
        self.ensure_integrity_check.setToolTip(self.tr("启用后，肯定语将在背景音乐中完整循环播放，不会被截断。如果肯定语比背景音乐长，将阻止生成。"))
        layout.addWidget(self.ensure_integrity_check, 10, 0, 1, 3)

        self.affirmation_group.setLayout(layout)
        return self.affirmation_group
    
    def create_background_group(self):
        """创建背景音组"""
        self.background_group = QGroupBox(self.tr("背景音"))
        layout = QGridLayout()

        # 文件选择
        self.label_bg_file = QLabel(self.tr("背景音文件:"))
        layout.addWidget(self.label_bg_file, 0, 0)
        self.background_file = QLineEdit()
        self.background_file.setToolTip(self.tr("选择一个音频文件作为背景音。"))
        layout.addWidget(self.background_file, 0, 1)

        self.btn_browse_bg = QPushButton(self.tr("浏览..."))
        self.btn_browse_bg.clicked.connect(lambda: self.browse_file(self.background_file,
                                                              self.tr("音频文件 (*.mp3 *.wav)")))
        self.btn_browse_bg.setToolTip(self.tr("选择背景音频文件"))
        layout.addWidget(self.btn_browse_bg, 0, 2)

        # 音量滑条
        self.label_bg_volume = QLabel(self.tr("音量:"))
        layout.addWidget(self.label_bg_volume, 1, 0)
        self.background_volume = QSlider(Qt.Horizontal)
        self.background_volume.setRange(-600, 0)
        self.background_volume.setValue(0)
        self.background_volume.setToolTip(self.tr("改变背景音音轨的音量。（单位为分贝）"))
        layout.addWidget(self.background_volume, 1, 1)

        self.background_volume_spin = QDoubleSpinBox()
        self.background_volume_spin.setRange(-60.0, 0.0)
        self.background_volume_spin.setValue(0.0)
        self.background_volume_spin.setSingleStep(0.5)
        self.background_volume_spin.valueChanged.connect(
            lambda v: self.background_volume.setValue(int(v * 10)))
        self.background_volume.valueChanged.connect(
            lambda v: self.background_volume_spin.setValue(v / 10.0))
        layout.addWidget(self.background_volume_spin, 1, 2)

        self.background_group.setLayout(layout)
        return self.background_group
    
    def create_freq_track_group(self):
        """创建特定频率音轨组"""
        self.freq_track_group = QGroupBox(self.tr("特定频率音轨"))
        layout = QGridLayout()

        # 启用特定频率音轨
        self.freq_track_enabled = QCheckBox(self.tr("启用特定频率音轨"))
        self.freq_track_enabled.setChecked(False)
        self.freq_track_enabled.setToolTip(self.tr("在音频中叠加特定频率的音轨。"))
        layout.addWidget(self.freq_track_enabled, 0, 0, 1, 3)

        # 频率选择
        self.label_freq_track_freq = QLabel(self.tr("频率 (Hz):"))
        layout.addWidget(self.label_freq_track_freq, 1, 0)
        self.freq_track_freq = QLineEdit()
        self.freq_track_freq.setText("432")
        self.freq_track_freq.setToolTip(self.tr("输入要叠加的特定频率(Hz)。"))
        layout.addWidget(self.freq_track_freq, 1, 1, 1, 2)

        # 音量设置
        self.label_freq_track_volume = QLabel(self.tr("音量 (dB):"))
        layout.addWidget(self.label_freq_track_volume, 2, 0)
        self.freq_track_volume = QDoubleSpinBox()
        self.freq_track_volume.setRange(-60.0, 0.0)
        self.freq_track_volume.setValue(-23.0)
        self.freq_track_volume.setSingleStep(1.0)
        self.freq_track_volume.setToolTip(self.tr("特定频率音轨的音量（分贝）。"))
        layout.addWidget(self.freq_track_volume, 2, 1, 1, 2)

        self.freq_track_group.setLayout(layout)
        return self.freq_track_group
    
    def create_output_group(self):
        """创建输出组"""
        self.output_group = QGroupBox(self.tr("输出"))
        layout = QGridLayout()

        row = 0

        # 生成音频复选框
        self.generate_audio = QCheckBox(self.tr("生成音频"))
        self.generate_audio.setChecked(True)
        self.generate_audio.setToolTip(self.tr("是否生成音频。"))
        self.generate_audio.toggled.connect(self.on_generate_audio_toggled)
        layout.addWidget(self.generate_audio, row, 0, 1, 2)

        # 音频设置组
        self.audio_group = QGroupBox(self.tr("音频设置"))
        audio_layout = QGridLayout()

        self.label_audio_format = QLabel(self.tr("格式:"))
        audio_layout.addWidget(self.label_audio_format, 0, 0)
        self.audio_format = QComboBox()
        self.audio_format.addItems(["WAV", "MP3"])
        audio_layout.addWidget(self.audio_format, 0, 1)

        self.label_audio_sample_rate = QLabel(self.tr("采样率:"))
        audio_layout.addWidget(self.label_audio_sample_rate, 1, 0)
        self.audio_sample_rate = QComboBox()
        self.audio_sample_rate.addItems(["44100 Hz", "48000 Hz", "96000 Hz", "192000 Hz"])
        audio_layout.addWidget(self.audio_sample_rate, 1, 1)

        self.audio_group.setLayout(audio_layout)
        layout.addWidget(self.audio_group, row+1, 0, 1, 3)

        row += 2

        # ffmpeg未安装提示
        self.ffmpeg_warning_label = QLabel()
        self.ffmpeg_warning_label.setText(self.tr('⚠️ 未检测到ffmpeg，视频生成和非WAV音频格式功能已被禁用。<a href="https://ffmpeg.org/download.html">点击下载ffmpeg</a>'))
        self.ffmpeg_warning_label.setStyleSheet("color: orange; font-weight: bold;")
        self.ffmpeg_warning_label.setVisible(False)
        self.ffmpeg_warning_label.setOpenExternalLinks(True)
        layout.addWidget(self.ffmpeg_warning_label, row, 0, 1, 3)

        row += 1

        # 生成视频复选框
        self.generate_video = QCheckBox(self.tr("生成视频"))
        self.generate_video.setToolTip(self.tr("是否生成视频。"))
        self.generate_video.toggled.connect(self.on_generate_video_toggled)
        layout.addWidget(self.generate_video, row, 0, 1, 2)

        # 视频设置组
        self.video_group = QGroupBox(self.tr("视频设置"))
        video_layout = QGridLayout()

        # 视觉化图片选择
        self.label_video_image = QLabel(self.tr("视觉化图片:"))
        video_layout.addWidget(self.label_video_image, 0, 0)
        self.video_image = QLineEdit()
        self.video_image.setToolTip(self.tr("选择一个图片文件作为视觉化。"))
        video_layout.addWidget(self.video_image, 0, 1, 1, 2)

        self.btn_browse_image = QPushButton(self.tr("浏览..."))
        self.btn_browse_image.clicked.connect(lambda: self.browse_file(self.video_image,
                                                                 self.tr("图片文件 (*.jpg *.jpeg *.png *.bmp)")))
        self.btn_browse_image.setToolTip(self.tr("选择视觉化图片"))
        video_layout.addWidget(self.btn_browse_image, 0, 3)

        # 搜索视觉化图片
        self.label_search_keyword = QLabel(self.tr("搜索关键词:"))
        video_layout.addWidget(self.label_search_keyword, 1, 0)
        self.search_keyword = QLineEdit()
        self.search_keyword.setToolTip(self.tr("输入关键词。"))
        video_layout.addWidget(self.search_keyword, 1, 1, 1, 2)

        # 搜索引擎选择
        self.label_search_engine = QLabel(self.tr("搜索引擎:"))
        video_layout.addWidget(self.label_search_engine, 2, 0)
        self.search_engine = QComboBox()
        self.search_engine.addItems(["Bing", "Google", "DuckDuckGo"])
        self.search_engine.setToolTip(self.tr("搜索视觉化图片时使用的搜索引擎。"))
        video_layout.addWidget(self.search_engine, 2, 1)

        # 联机搜索按钮
        self.search_btn = QPushButton(self.tr("联机搜索"))
        self.search_btn.setToolTip(self.tr("联机搜索视觉化图片。"))
        self.search_btn.clicked.connect(self.search_visualization_image)
        video_layout.addWidget(self.search_btn, 2, 2, 1, 2)

        # 视频格式设置
        self.label_video_format = QLabel(self.tr("视频格式:"))
        video_layout.addWidget(self.label_video_format, 3, 0)
        self.video_format = QComboBox()
        self.video_format.addItems(["MP4", "AVI", "MKV"])
        video_layout.addWidget(self.video_format, 3, 1)

        self.label_video_audio_sample_rate = QLabel(self.tr("音频采样率:"))
        video_layout.addWidget(self.label_video_audio_sample_rate, 4, 0)
        self.video_audio_sample_rate = QComboBox()
        self.video_audio_sample_rate.addItems(["44100 Hz", "48000 Hz", "96000 Hz"])
        video_layout.addWidget(self.video_audio_sample_rate, 4, 1)

        self.label_video_bitrate = QLabel(self.tr("码率:"))
        video_layout.addWidget(self.label_video_bitrate, 5, 0)
        self.video_bitrate = QComboBox()
        self.video_bitrate.addItems(["128 kbps", "192 kbps", "256 kbps", "320 kbps"])
        video_layout.addWidget(self.video_bitrate, 5, 1)

        self.label_video_resolution = QLabel(self.tr("分辨率:"))
        video_layout.addWidget(self.label_video_resolution, 6, 0)
        self.video_resolution = QComboBox()
        self.video_resolution.addItems(["1920x1080", "1280x720", "854x480", "640x360"])
        video_layout.addWidget(self.video_resolution, 6, 1)

        self.video_group.setLayout(video_layout)
        layout.addWidget(self.video_group, row+1, 0, 1, 3)

        row += 2

        # 必须选择至少一个提示
        self.selection_hint = QLabel(self.tr("* 必须至少选择生成音频或生成视频一项"))
        self.selection_hint.setStyleSheet("color: red;")
        layout.addWidget(self.selection_hint, row, 0, 1, 3)

        row += 1

        # 元数据组
        self.metadata_group = QGroupBox(self.tr("元数据"))
        metadata_layout = QGridLayout()

        self.label_metadata_title = QLabel(self.tr("标题:"))
        metadata_layout.addWidget(self.label_metadata_title, 0, 0)
        self.metadata_title = QLineEdit()
        self.metadata_title.setToolTip(self.tr("设置项目输出元数据中的标题。"))
        metadata_layout.addWidget(self.metadata_title, 0, 1)

        self.label_metadata_author = QLabel(self.tr("作者:"))
        metadata_layout.addWidget(self.label_metadata_author, 1, 0)
        self.metadata_author = QLineEdit()
        self.metadata_author.setToolTip(self.tr("设置项目输出元数据中的作者。"))
        metadata_layout.addWidget(self.metadata_author, 1, 1)

        self.metadata_group.setLayout(metadata_layout)
        layout.addWidget(self.metadata_group, row, 0, 1, 3)

        row += 1

        # 预览组
        self.preview_group = QGroupBox(self.tr("预览"))
        preview_layout = QVBoxLayout()

        # 预览控制按钮
        preview_control_layout = QHBoxLayout()

        self.preview_zoom_in_btn = QPushButton(self.tr("放大"))
        self.preview_zoom_in_btn.setToolTip(self.tr("放大预览视图"))
        self.preview_zoom_in_btn.clicked.connect(self.preview_zoom_in)
        preview_control_layout.addWidget(self.preview_zoom_in_btn)

        self.preview_zoom_out_btn = QPushButton(self.tr("缩小"))
        self.preview_zoom_out_btn.setToolTip(self.tr("缩小预览视图"))
        self.preview_zoom_out_btn.clicked.connect(self.preview_zoom_out)
        preview_control_layout.addWidget(self.preview_zoom_out_btn)

        self.preview_reset_btn = QPushButton(self.tr("重置视图"))
        self.preview_reset_btn.setToolTip(self.tr("重置预览视图缩放和位置"))
        self.preview_reset_btn.clicked.connect(self.preview_reset)
        preview_control_layout.addWidget(self.preview_reset_btn)

        self.preview_update_btn = QPushButton(self.tr("更新预览"))
        self.preview_update_btn.setToolTip(self.tr("根据当前配置更新预览"))
        self.preview_update_btn.clicked.connect(self.update_preview)
        preview_control_layout.addWidget(self.preview_update_btn)

        preview_control_layout.addStretch()
        preview_layout.addLayout(preview_control_layout)

        # 预览画布
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(False)  # 关闭自动调整大小，让内容控制尺寸
        self.preview_scroll.setMinimumHeight(200)
        self.preview_scroll.setStyleSheet("QScrollArea { border: 1px solid #ccc; background-color: #f5f5f5; }")

        self.preview_widget = QWidget()
        self.preview_widget.setMinimumSize(800, 300)
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setSpacing(10)
        self.preview_layout.setContentsMargins(10, 10, 10, 10)

        # 轨道标签
        self.preview_tracks_label = QLabel(self.tr('轨道预览（点击"更新预览"查看）'))
        self.preview_tracks_label.setAlignment(Qt.AlignCenter)
        self.preview_tracks_label.setStyleSheet("color: #666; font-size: 12px;")
        self.preview_layout.addWidget(self.preview_tracks_label)

        self.preview_scroll.setWidget(self.preview_widget)
        preview_layout.addWidget(self.preview_scroll)

        # 缩放比例显示
        self.preview_zoom_label = QLabel(self.tr("缩放: 100%"))
        self.preview_zoom_label.setAlignment(Qt.AlignRight)
        preview_layout.addWidget(self.preview_zoom_label)

        self.preview_group.setLayout(preview_layout)
        layout.addWidget(self.preview_group, row, 0, 1, 3)

        row += 1

        # 生成按钮
        self.generate_btn = QPushButton(self.tr("生成项目"))
        self.generate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-size: 14pt; padding: 10px; }")
        self.generate_btn.setToolTip(self.tr("开始生成项目！"))
        self.generate_btn.clicked.connect(self.generate_project)
        layout.addWidget(self.generate_btn, row, 0, 1, 3)

        self.output_group.setLayout(layout)
        return self.output_group

    def on_generate_audio_toggled(self, checked):
        """生成音频复选框状态变化处理"""
        # 如果取消勾选音频，且视频也未勾选，则阻止取消勾选并提示
        if not checked and not self.generate_video.isChecked():
            # 阻止信号递归
            self.generate_audio.blockSignals(True)
            self.generate_audio.setChecked(True)
            self.generate_audio.blockSignals(False)
            QMessageBox.warning(self, self.tr("提示"), self.tr("必须至少选择生成音频或生成视频一项！"))

    def on_generate_video_toggled(self, checked):
        """生成视频复选框状态变化处理"""
        # 如果取消勾选视频，且音频也未勾选，则阻止取消勾选并提示
        if not checked and not self.generate_audio.isChecked():
            # 阻止信号递归
            self.generate_video.blockSignals(True)
            self.generate_video.setChecked(True)
            self.generate_video.blockSignals(False)
            QMessageBox.warning(self, self.tr("提示"), self.tr("必须至少选择生成音频或生成视频一项！"))

    def browse_file(self, line_edit, file_filter):
        """浏览文件对话框"""
        logger.debug(f"打开文件浏览对话框 - 过滤器: {file_filter}")
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("选择文件"), "", file_filter)
        if file_path:
            logger.debug(f"选择的文件路径: {file_path}")
            logger.debug(f"文件绝对路径: {os.path.abspath(file_path)}")
            logger.debug(f"文件是否存在: {os.path.exists(file_path)}")
            if os.path.exists(file_path):
                logger.debug(f"文件大小: {os.path.getsize(file_path)} bytes")
            line_edit.setText(file_path)
            # 如果是文本文件输入框，自动加载文件内容
            if line_edit == self.text_file:
                self.text_sync.load_text_from_file(file_path)

    def toggle_recording(self):
        """切换录音状态（开始/停止录制）"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录制音频"""
        # 检查是否选择了项目
        if not self.check_project_selected():
            self.record_btn.setChecked(False)
            return

        try:
            # 获取选中的录音设备
            device_index = None

            # 如果不是系统默认，获取设备索引（存储在itemData中）
            if self.record_device.currentText() != self.tr("系统默认"):
                device_index = self.record_device.currentData()
                if device_index is None:
                    # 兼容旧逻辑：如果data为None，尝试通过名称查找
                    device_name = self.record_device.currentText()
                    p = pyaudio.PyAudio()
                    for i in range(p.get_device_count()):
                        device_info = p.get_device_info_by_index(i)
                        if device_info['name'].strip() == device_name and device_info['maxInputChannels'] > 0:
                            device_index = i
                            break
                    p.terminate()

            # 创建输出目录
            output_dir = self.get_affirmation_output_dir()
            if not output_dir:
                QMessageBox.critical(self, self.tr("错误"),
                                   self.tr("无法获取项目目录！"))
                self.record_btn.setChecked(False)
                return

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 生成输出文件名（使用时间戳）
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"recorded_{timestamp}.wav")

            # 创建录音器
            self.recorder = AudioRecorder(device_index=device_index)
            self.recorder.set_output_file(output_file)
            self.recorder.recording_finished.connect(self.on_recording_finished)
            self.recorder.recording_error.connect(self.on_recording_error)

            # 开始录制
            self.recorder.start()
            self.is_recording = True

            # 更新按钮状态
            self.record_btn.setText(self.tr("停止录制"))
            self.record_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")

            logger.info(f"开始录制，输出文件: {output_file}")

        except Exception as e:
            logger.error(f"开始录制失败: {e}")
            QMessageBox.critical(self, self.tr("错误"), self.tr(f"开始录制失败: {str(e)}"))
            self.record_btn.setChecked(False)

    def stop_recording(self):
        """停止录制音频"""
        if self.recorder and self.is_recording:
            self.recorder.stop()
            self.recorder.wait()  # 等待线程结束

        self.is_recording = False

        # 恢复按钮状态
        self.record_btn.setText(self.tr("开始录制"))
        self.record_btn.setStyleSheet("")
        self.record_btn.setChecked(False)

        logger.info("停止录制")

    def on_recording_finished(self, file_path):
        """录音完成回调"""
        # 更新音频文件路径输入框
        self.affirmation_file.setText(file_path)

        logger.info(f"录音完成，文件已保存: {file_path}")
        QMessageBox.information(self, self.tr("成功"),
                                self.tr(f"录音完成！文件已保存到: {file_path}"))

    def on_recording_error(self, error_msg):
        """录音错误回调"""
        self.is_recording = False

        # 恢复按钮状态
        self.record_btn.setText(self.tr("开始录制"))
        self.record_btn.setStyleSheet("")
        self.record_btn.setChecked(False)

        logger.error(f"录音出错: {error_msg}")
        QMessageBox.critical(self, self.tr("错误"), self.tr(f"录音出错: {error_msg}"))
    
    def search_visualization_image(self):
        """联机搜索视觉化图片"""
        keyword = self.search_keyword.text().strip()
        if not keyword:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请输入搜索关键词！"))
            return

        # 获取选中的搜索引擎
        search_engine = self.search_engine.currentText()

        # 构建搜索URL
        if search_engine == "Bing":
            url = f"https://www.bing.com/images/search?q={keyword}"
        elif search_engine == "Google":
            url = f"https://www.google.com/search?tbm=isch&q={keyword}"
        elif search_engine == "DuckDuckGo":
            url = f"https://duckduckgo.com/?iax=images&ia=images&q={keyword}"
        else:
            url = f"https://www.bing.com/images/search?q={keyword}"

        # 使用系统默认浏览器打开
        import webbrowser
        webbrowser.open(url)
        logger.info(f"打开浏览器搜索: {url}")

    def get_audio_duration(self, file_path):
        """获取音频文件时长（秒）"""
        try:
            import os
            # 检查文件是否存在
            if not file_path or not os.path.exists(file_path):
                logger.error(f"音频文件不存在: {file_path}")
                return None
            
            import subprocess
            import json
            # 确保路径格式正确
            file_path = os.path.abspath(file_path)
            cmd = [
                'ffmpeg', '-i', file_path,
                '-f', 'json', '-show_entries', 'format=duration',
                '-loglevel', 'quiet'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output = json.loads(result.stdout)
                duration = float(output['format']['duration'])
                return duration
            else:
                # 如果ffmpeg失败，尝试使用wave模块（仅WAV文件）
                import wave
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    return frames / float(rate)
        except Exception as e:
            logger.error(f"获取音频时长失败: {file_path}, 错误: {e}")
            return None

    def validate_affirmation_integrity(self):
        """验证肯定语完整性
        当启用确保完整性时，检查肯定语是否比背景音乐长
        如果肯定语更长，阻止生成并提示用户
        """
        affirmation_file = self.affirmation_file.text()
        background_file = self.background_file.text()

        if not affirmation_file or not os.path.exists(affirmation_file):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("肯定语音频文件不存在！"))
            return False

        # 如果没有背景音乐，不需要检查
        if not background_file or not os.path.exists(background_file):
            return True

        # 获取音频时长
        aff_duration = self.get_audio_duration(affirmation_file)
        bg_duration = self.get_audio_duration(background_file)

        if aff_duration is None:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("无法读取肯定语音频文件！"))
            return False

        if bg_duration is None:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("无法读取背景音频文件！"))
            return False

        # 计算应用倍速后的肯定语时长
        speed = self.speed_spin.value()
        adjusted_aff_duration = aff_duration / speed

        # 计算叠加后的总时长
        overlay_times = self.overlay_times.value()
        overlay_interval = self.overlay_interval.value()
        total_aff_duration = adjusted_aff_duration + (overlay_times - 1) * overlay_interval

        logger.info(f"验证完整性: 肯定语时长={adjusted_aff_duration:.2f}s, "
                   f"叠加后总时长={total_aff_duration:.2f}s, 背景音乐时长={bg_duration:.2f}s")

        if total_aff_duration > bg_duration:
            warning_msg = self.tr("启用'确保肯定语完整性'时，肯定语（含叠加效果）不能比背景音乐长。\n\n"
                                 f"肯定语时长: {total_aff_duration:.2f}秒\n"
                                 f"背景音乐时长: {bg_duration:.2f}秒\n\n"
                                 f"请缩短肯定语、减少叠加次数、减小叠加间隔，或选择更长的背景音乐。")
            logger.warning(f"肯定语比背景音乐长，阻止生成: {total_aff_duration:.2f}s > {bg_duration:.2f}s")
            QMessageBox.warning(self, self.tr("无法生成"), warning_msg)
            return False

        return True

    def generate_project(self):
        """生成项目"""
        logger.debug("开始生成项目")

        # 验证至少选择了一项
        if not self.generate_audio.isChecked() and not self.generate_video.isChecked():
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("必须至少选择生成音频或生成视频一项！"))
            return

        # 验证必要文件
        affirmation_file = self.affirmation_file.text()
        if self.generate_audio.isChecked() and not affirmation_file:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("生成音频需要选择肯定语音频文件！"))
            return

        logger.debug(f"肯定语文件路径: {affirmation_file}")
        if affirmation_file:
            logger.debug(f"肯定语文件绝对路径: {os.path.abspath(affirmation_file)}")
            logger.debug(f"肯定语文件是否存在: {os.path.exists(affirmation_file)}")

        # 检查是否选择了项目
        if not self.check_project_selected():
            return

        # 获取项目目录
        project_dir = self.get_current_project_dir()

        # 保存项目配置
        self.save_project_config(project_dir)

        # 如果启用了确保完整性检查，进行前置验证
        if self.ensure_integrity_check.isChecked():
            if not self.validate_affirmation_integrity():
                return

        # 获取输出路径
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 判断是否生成音频文件
        generate_audio = self.generate_audio.isChecked()
        generate_video = self.generate_video.isChecked()

        logger.debug(f"生成选项 - 音频: {generate_audio}, 视频: {generate_video}")

        # 获取选择的音频格式
        audio_format = self.audio_format.currentText()
        format_ext = audio_format.lower()

        # 如果只生成视频不生成音频，使用临时文件路径
        if generate_video and not generate_audio:
            # 使用临时目录存放音频文件
            import tempfile
            temp_dir = tempfile.gettempdir()
            audio_output_path = os.path.join(temp_dir, f"SMake_temp_audio_{timestamp}.wav")
            logger.debug(f"使用临时音频路径: {audio_output_path}")
        else:
            # 正常保存到项目目录，使用选择的格式扩展名
            audio_output_path = os.path.join(project_dir, "Releases", "Audio", f"{timestamp}.{format_ext}")
            logger.debug(f"使用项目音频路径: {audio_output_path}")

        # 确保输出目录存在
        output_dir = os.path.dirname(audio_output_path)
        if output_dir and not os.path.exists(output_dir):
            logger.debug(f"创建输出目录: {os.path.abspath(output_dir)}")
            os.makedirs(output_dir, exist_ok=True)

        # 准备参数
        params = {
            'affirmation_file': affirmation_file,
            'background_file': self.background_file.text(),
            'volume': self.affirmation_volume_spin.value(),
            'frequency_mode': self.frequency_mode.currentIndex(),
            'speed': self.speed_spin.value(),
            'reverse': self.reverse_check.isChecked(),
            'overlay_times': self.overlay_times.value(),
            'overlay_interval': self.overlay_interval.value(),
            'volume_decrease': self.volume_decrease.value(),
            'background_volume': self.background_volume_spin.value(),
            'freq_track_enabled': self.freq_track_enabled.isChecked(),
            'freq_track_freq': self.freq_track_freq.text(),
            'freq_track_volume': self.freq_track_volume.value(),
            'output_format': self.audio_format.currentText(),
            'output_path': audio_output_path,
            'generate_audio': generate_audio,
            'generate_video': generate_video,
            'video_image': self.video_image.text(),
            'video_format': self.video_format.currentText(),
            'video_resolution': self.video_resolution.currentText(),
            'metadata_title': self.metadata_title.text(),
            'metadata_author': self.metadata_author.text(),
            'ensure_integrity': self.ensure_integrity_check.isChecked()
        }

        logger.debug(f"生成项目参数 - output_path: {audio_output_path}")
        logger.debug(f"生成项目参数 - affirmation_file: {affirmation_file}")
        logger.debug(f"生成项目参数 - background_file: {self.background_file.text()}")
        logger.debug(f"生成项目参数 - video_image: {self.video_image.text()}")
        logger.debug(f"生成项目参数 - freq_track_enabled: {params['freq_track_enabled']}")
        logger.debug(f"生成项目参数 - freq_track_freq: {params['freq_track_freq']}")
        logger.debug(f"生成项目参数 - freq_track_volume: {params['freq_track_volume']}")

        # 创建进度对话框
        self.progress_dialog = QProgressDialog(self.tr("正在生成项目..."), self.tr("取消"), 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self.cancel_generation)
        self.progress_dialog.show()

        # 保存参数供后续视频生成使用
        self.current_generation_params = params

        # 创建并启动音频处理线程
        self.audio_processor = AudioProcessor(params)
        self.audio_processor.progress_updated.connect(self.update_progress)
        self.audio_processor.processing_finished.connect(self.on_generation_finished)
        self.audio_processor.processing_error.connect(self.on_generation_error)
        self.audio_processor.start()

        logger.info("开始生成项目")

    def update_progress(self, value):
        """更新进度"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(value)

    def cancel_generation(self):
        """取消生成"""
        if hasattr(self, 'audio_processor') and self.audio_processor and self.audio_processor.isRunning():
            self.audio_processor.cancel()
            self.audio_processor.wait()
            logger.info("用户取消音频生成")

        if hasattr(self, 'video_processor') and self.video_processor and self.video_processor.isRunning():
            self.video_processor.cancel()
            self.video_processor.wait()
            logger.info("用户取消视频生成")

    def on_generation_finished(self, output_path):
        """生成完成回调"""
        logger.info(f"音频生成完成: {output_path}")

        # 检查是否需要生成视频
        if hasattr(self, 'current_generation_params') and self.current_generation_params.get('generate_video'):
            # 需要生成视频，继续视频生成流程
            self.start_video_generation(output_path)
        else:
            # 不需要生成视频，直接完成
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                # 断开canceled信号，避免关闭对话框时触发cancel_generation
                try:
                    self.progress_dialog.canceled.disconnect(self.cancel_generation)
                except:
                    pass
                self.progress_dialog.close()
                self.progress_dialog = None

            # 显示成功消息
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"音频生成成功！\n保存路径: {output_path}"))

    def start_video_generation(self, audio_path):
        """开始视频生成"""
        try:
            params = self.current_generation_params
            project_dir = self.get_current_project_dir()
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            logger.debug(f"start_video_generation - audio_path: {audio_path}")
            logger.debug(f"start_video_generation - audio_path绝对路径: {os.path.abspath(audio_path)}")
            logger.debug(f"start_video_generation - audio_path是否存在: {os.path.exists(audio_path)}")

            # 确定视频格式扩展名
            video_format = params.get('video_format', 'MP4')
            format_ext = {
                'MP4': '.mp4',
                'AVI': '.avi',
                'MKV': '.mkv'
            }.get(video_format, '.mp4')

            video_output_path = os.path.join(project_dir, "Releases", "Video", f"{timestamp}{format_ext}")
            logger.debug(f"视频输出路径: {video_output_path}")
            logger.debug(f"视频输出绝对路径: {os.path.abspath(video_output_path)}")

            # 确保视频输出目录存在
            video_output_dir = os.path.dirname(video_output_path)
            if video_output_dir and not os.path.exists(video_output_dir):
                logger.debug(f"创建视频输出目录: {os.path.abspath(video_output_dir)}")
                os.makedirs(video_output_dir, exist_ok=True)

            # 准备视频生成参数
            video_image = params.get('video_image')
            video_params = {
                'audio_path': audio_path,
                'video_image': video_image,
                'video_output_path': video_output_path,
                'video_format': video_format,
                'video_resolution': params.get('video_resolution', '1920x1080'),
                'metadata_title': params.get('metadata_title', ''),
                'metadata_author': params.get('metadata_author', '')
            }

            logger.debug(f"视频生成参数 - video_image: {video_image}")
            if video_image:
                logger.debug(f"视频生成参数 - video_image绝对路径: {os.path.abspath(video_image)}")
                logger.debug(f"视频生成参数 - video_image是否存在: {os.path.exists(video_image)}")

            logger.info(f"开始视频生成: {video_output_path}")

            # 更新进度对话框
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.setLabelText(self.tr("正在生成视频..."))
                self.progress_dialog.setValue(0)

            # 创建并启动视频处理线程
            self.video_processor = VideoProcessor(video_params)
            self.video_processor.progress_updated.connect(self.update_progress)
            self.video_processor.processing_finished.connect(self.on_video_generation_finished)
            self.video_processor.processing_error.connect(self.on_video_generation_error)
            self.video_processor.start()

        except Exception as e:
            logger.error(f"启动视频生成失败: {e}")

            # 如果只生成视频不生成音频，删除临时音频文件
            generate_audio = params.get('generate_audio', False)
            if not generate_audio and audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.info(f"删除临时音频文件: {audio_path}")
                except Exception as del_e:
                    logger.warning(f"删除临时音频文件失败: {del_e}")

            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                try:
                    self.progress_dialog.canceled.disconnect(self.cancel_generation)
                except:
                    pass
                self.progress_dialog.close()
                self.progress_dialog = None

            QMessageBox.critical(self, self.tr("错误"),
                                self.tr(f"视频生成失败。\n错误: {str(e)}"))

    def on_video_generation_finished(self, video_path):
        """视频生成完成回调"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            try:
                self.progress_dialog.canceled.disconnect(self.cancel_generation)
            except:
                pass
            self.progress_dialog.close()
            self.progress_dialog = None

        logger.info(f"视频生成完成: {video_path}")

        # 获取音频路径
        audio_path = self.current_generation_params.get('output_path', '')
        generate_audio = self.current_generation_params.get('generate_audio', False)

        # 如果只生成视频不生成音频，删除临时音频文件
        if not generate_audio and audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"删除临时音频文件: {audio_path}")
            except Exception as e:
                logger.warning(f"删除临时音频文件失败: {e}")

        # 显示成功消息
        if generate_audio:
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"音频和视频生成成功！\n\n音频: {audio_path}\n视频: {video_path}"))
        else:
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"视频生成成功！\n保存路径: {video_path}"))

    def on_video_generation_error(self, error_msg):
        """视频生成错误回调"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            try:
                self.progress_dialog.canceled.disconnect(self.cancel_generation)
            except:
                pass
            self.progress_dialog.close()
            self.progress_dialog = None

        logger.error(f"视频生成失败: {error_msg}")

        # 获取音频路径和生成选项
        audio_path = self.current_generation_params.get('output_path', '')
        generate_audio = self.current_generation_params.get('generate_audio', False)

        # 如果只生成视频不生成音频，删除临时音频文件
        if not generate_audio and audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"删除临时音频文件: {audio_path}")
            except Exception as e:
                logger.warning(f"删除临时音频文件失败: {e}")

        # 显示错误消息
        QMessageBox.critical(self, self.tr("错误"),
                            self.tr(f"视频生成失败。\n错误: {error_msg}"))

    def on_generation_error(self, error_msg):
        """生成错误回调"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            # 断开canceled信号，避免关闭对话框时触发cancel_generation
            try:
                self.progress_dialog.canceled.disconnect(self.cancel_generation)
            except:
                pass
            self.progress_dialog.close()
            self.progress_dialog = None

        logger.error(f"项目生成失败: {error_msg}")
        QMessageBox.critical(self, self.tr("错误"),
                            self.tr(f"生成失败: {error_msg}"))
    
    def get_available_translations(self):
        """获取所有可用的翻译文件"""
        translations = {}
        base_dir = self.get_resource_path()
        translation_dir = os.path.join(base_dir, "Translation")
        if os.path.exists(translation_dir):
            for filename in os.listdir(translation_dir):
                if filename.endswith('.qm'):
                    lang_code = filename[:-3]  # 移除 .qm 后缀
                    file_path = os.path.join(translation_dir, filename)
                    translations[lang_code] = file_path
        return translations

    def create_settings_group(self):
        """创建设置组"""
        self.settings_group = QGroupBox(self.tr("设置"))
        layout = QGridLayout()

        # 语言设置
        self.label_language = QLabel(self.tr("语言:"))
        layout.addWidget(self.label_language, 0, 0)
        self.language_combo = QComboBox()

        # 动态加载所有可用的翻译文件
        available_translations = self.get_available_translations()
        for lang_code in sorted(available_translations.keys()):
            self.language_combo.addItem(lang_code, lang_code)

        # 设置当前选中的语言
        current_index = self.language_combo.findData(self.current_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)

        self.language_combo.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.language_combo, 0, 1)

        # 应用语言按钮
        self.apply_language_btn = QPushButton(self.tr("应用语言"))
        self.apply_language_btn.clicked.connect(self.apply_language_settings)
        layout.addWidget(self.apply_language_btn, 0, 2)

        # 重置设置按钮
        self.reset_settings_btn = QPushButton(self.tr("重置设置"))
        self.reset_settings_btn.clicked.connect(self.reset_settings)
        layout.addWidget(self.reset_settings_btn, 1, 0, 1, 3)

        # 关于信息
        self.about_group = QGroupBox(self.tr("关于"))
        about_layout = QVBoxLayout()

        self.about_label = QLabel(self.tr("SMake"))
        self.about_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(self.about_label)

        self.about_group.setLayout(about_layout)
        layout.addWidget(self.about_group, 2, 0, 1, 3)

        self.settings_group.setLayout(layout)
        return self.settings_group
    
    def change_language(self, index):
        """语言选择改变"""
        self.new_language = self.language_combo.itemData(index)
        logger.debug(f"语言选择改变: {self.new_language}")
    
    def apply_language_settings(self):
        """应用语言设置"""
        logger.info("开始应用语言设置")
        
        if hasattr(self, 'new_language') and self.new_language:
            logger.info(f"应用新语言设置: {self.new_language}")
            
            # 保存语言设置
            self.settings.setValue("language", self.new_language)
            self.current_language = self.new_language
            
            # 重新加载翻译
            self.setupTranslations()
            
            logger.info("语言设置应用完成")
            
        else:
            logger.warning("未选择语言")
            QMessageBox.warning(self, self.tr("警告"), 
                               self.tr("请先选择语言！"))
    
    def reset_settings(self):
        """重置所有设置"""
        reply = QMessageBox.question(self, self.tr("确认重置"), 
                                    self.tr("确定要重置所有设置吗？这将恢复所有设置为默认值。"),
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            logger.info("开始重置设置")
            # 清除所有设置
            self.settings.clear()
            logger.debug("设置已清空")
            
            # 重置语言为默认
            self.current_language = "zh_CN"
            self.settings.setValue("language", self.current_language)
            logger.info(f"语言重置为默认: {self.current_language}")
            
            # 重新加载翻译
            self.setupTranslations()
            
            # 更新语言选择框
            current_index = self.language_combo.findData(self.current_language)
            if current_index >= 0:
                self.language_combo.setCurrentIndex(current_index)
            
            logger.info("设置重置完成")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr("所有设置已重置为默认值。"))

    def create_log_group(self):
        """创建日志输出组"""
        self.log_group = QGroupBox(self.tr("日志输出"))
        layout = QVBoxLayout()

        # 日志显示区域
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_text_edit)

        # 清空日志按钮
        button_layout = QGridLayout()
        self.clear_log_btn = QPushButton(self.tr("清空日志"))
        self.clear_log_btn.setToolTip(self.tr("清空日志显示区域"))
        self.clear_log_btn.clicked.connect(self.clear_log_display)
        button_layout.addWidget(self.clear_log_btn, 0, 0)

        # 添加弹性空间
        button_layout.setColumnStretch(1, 1)
        layout.addLayout(button_layout)

        self.log_group.setLayout(layout)
        return self.log_group

    def clear_log_display(self):
        """清空日志显示区域"""
        if hasattr(self, 'log_text_edit'):
            self.log_text_edit.clear()
            logger.info("日志显示区域已清空")

    def append_log_message(self, message):
        """添加日志消息到显示区域
        
        Args:
            message: 日志消息内容（原始格式）
        """
        if not hasattr(self, 'log_text_edit'):
            return

        # 直接显示原始消息，不做任何颜色或格式处理
        self.log_text_edit.append(message)

        # 自动滚动到底部
        scrollbar = self.log_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ==================== 项目管理方法 ====================

    def load_project_config(self, project_dir):
        """加载项目配置文件
        
        Args:
            project_dir: 项目目录路径
        """
        config_path = os.path.join(project_dir, "config.json")
        logger.debug(f"尝试加载项目配置: {config_path}")

        if not os.path.exists(config_path):
            logger.info(f"项目配置文件不存在，使用默认配置: {config_path}")
            # 清空元数据字段
            if hasattr(self, 'metadata_title') and self.metadata_title is not None:
                self.metadata_title.clear()
            if hasattr(self, 'metadata_author') and self.metadata_author is not None:
                self.metadata_author.clear()
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 加载元数据
            metadata = config.get('metadata', {})
            if hasattr(self, 'metadata_title') and self.metadata_title is not None:
                self.metadata_title.setText(metadata.get('title', ''))
            if hasattr(self, 'metadata_author') and self.metadata_author is not None:
                self.metadata_author.setText(metadata.get('author', ''))

            logger.info(f"项目配置加载成功: {config_path}")
            logger.debug(f"配置内容: {config}")

        except json.JSONDecodeError as e:
            logger.error(f"项目配置文件格式错误: {config_path}, 错误: {e}")
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr(f"项目配置文件格式错误，将使用默认配置。"))
        except Exception as e:
            logger.error(f"加载项目配置失败: {config_path}, 错误: {e}")

    def save_project_config(self, project_dir):
        """保存项目配置文件
        
        Args:
            project_dir: 项目目录路径
        """
        config_path = os.path.join(project_dir, "config.json")
        logger.debug(f"保存项目配置: {config_path}")

        try:
            # 构建配置数据
            config = {
                "version": "1.0",
                "metadata": {
                    "title": self.metadata_title.text() if hasattr(self, 'metadata_title') else "",
                    "author": self.metadata_author.text() if hasattr(self, 'metadata_author') else ""
                }
            }

            # 写入JSON文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info(f"项目配置保存成功: {config_path}")

        except Exception as e:
            logger.error(f"保存项目配置失败: {config_path}, 错误: {e}")

    def get_project_base_dir(self):
        """获取项目基础目录"""
        # 项目目录需要存储在用户可写的位置，而不是打包的临时目录
        import sys
        import platform

        # 检测是否在 AppImage 环境中运行
        # AppImage 会设置 APPIMAGE 环境变量
        is_appimage = os.environ.get('APPIMAGE') is not None
        
        # 检测是否是 PyInstaller 打包的 Windows exe
        is_pyinstaller = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        
        if is_appimage:
            # AppImage 环境：sys.executable 指向挂载的只读目录
            # 使用当前工作目录作为项目存储位置
            cwd = os.getcwd()
            project_dir = os.path.join(cwd, "Project")
            logger.debug(f"AppImage 模式项目目录: {project_dir}")
            return project_dir
        elif is_pyinstaller:
            # PyInstaller 打包的 Windows exe
            # 使用可执行文件所在目录（Windows 上通常是可写的）
            exe_dir = os.path.dirname(sys.executable)
            project_dir = os.path.join(exe_dir, "Project")
            logger.debug(f"PyInstaller 模式项目目录: {project_dir}")
            return project_dir
        else:
            # 开发版本：使用项目根目录
            project_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Project")
            logger.debug(f"开发模式项目目录: {project_dir}")
            return project_dir

    def get_current_project_dir(self):
        """获取当前项目目录"""
        if hasattr(self, 'current_project_name') and self.current_project_name:
            # 支持项目组：项目路径为 基础目录/项目组/项目
            if hasattr(self, 'current_project_group') and self.current_project_group:
                project_dir = os.path.join(self.get_project_base_dir(), self.current_project_group, self.current_project_name)
            else:
                # 兼容旧版本：直接在基础目录下
                project_dir = os.path.join(self.get_project_base_dir(), self.current_project_name)
            logger.debug(f"获取当前项目目录: {project_dir}")
            logger.debug(f"项目目录绝对路径: {os.path.abspath(project_dir)}")
            logger.debug(f"项目目录是否存在: {os.path.exists(project_dir)}")
            return project_dir
        logger.debug("没有当前项目，返回None")
        return None

    def get_current_project_group_dir(self):
        """获取当前项目组目录"""
        if hasattr(self, 'current_project_group') and self.current_project_group:
            group_dir = os.path.join(self.get_project_base_dir(), self.current_project_group)
            logger.debug(f"获取当前项目组目录: {group_dir}")
            return group_dir
        # 默认返回基础目录
        return self.get_project_base_dir()

    def export_project(self):
        """导出当前项目"""
        if not self.current_project_name:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请先选择一个项目！"))
            return

        project_dir = self.get_current_project_dir()
        if not project_dir or not os.path.exists(project_dir):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("项目目录不存在！"))
            return

        # 选择导出格式和路径
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("导出项目"),
            f"{self.current_project_name}.zip",
            self.tr("ZIP 文件 (*.zip);;TAR.XZ 文件 (*.tar.xz)")
        )

        if not file_path:
            return

        try:
            # 根据选择的过滤器确定格式
            if "tar.xz" in selected_filter.lower() or file_path.endswith('.tar.xz'):
                # 使用 tar.xz 格式
                if not file_path.endswith('.tar.xz'):
                    file_path += '.tar.xz'
                self._compress_to_tar_xz(project_dir, file_path)
            else:
                # 默认使用 zip 格式
                if not file_path.endswith('.zip'):
                    file_path += '.zip'
                self._compress_to_zip(project_dir, file_path)

            logger.info(f"项目导出成功: {file_path}")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目 '{self.current_project_name}' 导出成功！\n保存位置: {file_path}"))

        except Exception as e:
            logger.error(f"导出项目失败: {e}")
            QMessageBox.critical(self, self.tr("错误"),
                               self.tr(f"导出项目失败: {str(e)}"))

    def export_project_group(self):
        """导出当前项目组"""
        if not self.current_project_group:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请先选择一个项目组！"))
            return

        group_dir = self.get_current_project_group_dir()
        if not group_dir or not os.path.exists(group_dir):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("项目组目录不存在！"))
            return

        # 选择导出格式和路径
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("导出项目组"),
            f"{self.current_project_group}.zip",
            self.tr("ZIP 文件 (*.zip);;TAR.XZ 文件 (*.tar.xz)")
        )

        if not file_path:
            return

        try:
            # 根据选择的过滤器确定格式
            if "tar.xz" in selected_filter.lower() or file_path.endswith('.tar.xz'):
                # 使用 tar.xz 格式
                if not file_path.endswith('.tar.xz'):
                    file_path += '.tar.xz'
                self._compress_to_tar_xz(group_dir, file_path)
            else:
                # 默认使用 zip 格式
                if not file_path.endswith('.zip'):
                    file_path += '.zip'
                self._compress_to_zip(group_dir, file_path)

            logger.info(f"项目组导出成功: {file_path}")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目组 '{self.current_project_group}' 导出成功！\n保存位置: {file_path}"))

        except Exception as e:
            logger.error(f"导出项目组失败: {e}")
            QMessageBox.critical(self, self.tr("错误"),
                               self.tr(f"导出项目组失败: {str(e)}"))

    def _compress_to_zip(self, source_dir, output_path):
        """将目录压缩为ZIP文件
        
        Args:
            source_dir: 源目录路径
            output_path: 输出ZIP文件路径
        """
        import zipfile

        logger.debug(f"开始压缩为ZIP: {source_dir} -> {output_path}")

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    logger.debug(f"添加文件到ZIP: {arcname}")

        logger.info(f"ZIP压缩完成: {output_path}")

    def _compress_to_tar_xz(self, source_dir, output_path):
        """将目录压缩为TAR.XZ文件
        
        Args:
            source_dir: 源目录路径
            output_path: 输出tar.xz文件路径
        """
        import tarfile

        logger.debug(f"开始压缩为TAR.XZ: {source_dir} -> {output_path}")

        with tarfile.open(output_path, "w:xz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

        logger.info(f"TAR.XZ压缩完成: {output_path}")

    def import_project_or_group(self):
        """导入项目或项目组"""
        # 选择要导入的文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("导入项目/项目组"),
            "",
            self.tr("压缩文件 (*.zip *.tar.xz)")
        )

        if not file_path:
            return

        try:
            # 确定导入类型
            import_type = self._detect_import_type(file_path)

            if import_type == "project":
                self._import_project(file_path)
            elif import_type == "group":
                self._import_project_group(file_path)
            else:
                # 无法自动检测，询问用户
                reply = QMessageBox.question(
                    self,
                    self.tr("选择导入类型"),
                    self.tr("无法自动检测导入类型。请选择要导入为项目还是项目组？"),
                    self.tr("项目"),
                    self.tr("项目组")
                )
                if reply == 0:  # 项目
                    self._import_project(file_path)
                else:  # 项目组
                    self._import_project_group(file_path)

        except Exception as e:
            logger.error(f"导入失败: {e}")
            QMessageBox.critical(self, self.tr("错误"),
                               self.tr(f"导入失败: {str(e)}"))

    def _detect_import_type(self, file_path):
        """检测导入文件类型（项目还是项目组）
        
        Args:
            file_path: 压缩文件路径
            
        Returns:
            str: "project", "group" 或 "unknown"
        """
        logger.debug(f"检测导入类型: {file_path}")

        try:
            if file_path.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as zf:
                    file_list = zf.namelist()
            elif file_path.endswith('.tar.xz'):
                import tarfile
                with tarfile.open(file_path, 'r:xz') as tf:
                    file_list = [m.name for m in tf.getmembers()]
            else:
                return "unknown"

            # 检查顶层目录结构
            top_dirs = set()
            for name in file_list:
                parts = name.split('/')
                if len(parts) > 0 and parts[0]:
                    top_dirs.add(parts[0])

            # 如果只有一个顶层目录，检查其内容
            if len(top_dirs) == 1:
                top_dir = list(top_dirs)[0]
                # 检查是否包含项目特征文件
                has_config = any('config.json' in f for f in file_list)
                has_assets = any('Assets/' in f for f in file_list)
                has_readme = any('README.md' in f for f in file_list)

                if has_config and has_assets:
                    return "project"

                # 检查是否包含子目录（可能是项目组）
                subdirs = set()
                for name in file_list:
                    parts = name.split('/')
                    if len(parts) > 1 and parts[1]:
                        subdirs.add(parts[1])

                if len(subdirs) > 0:
                    return "group"

            return "unknown"

        except Exception as e:
            logger.error(f"检测导入类型失败: {e}")
            return "unknown"

    def _import_project(self, file_path):
        """导入项目
        
        Args:
            file_path: 压缩文件路径
        """
        logger.info(f"开始导入项目: {file_path}")

        # 检查是否选择了项目组
        if not self.current_project_group:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请先选择一个项目组来导入项目！"))
            return

        target_dir = self.get_current_project_group_dir()

        # 解压文件
        if file_path.endswith('.zip'):
            self._extract_zip(file_path, target_dir)
        elif file_path.endswith('.tar.xz'):
            self._extract_tar_xz(file_path, target_dir)

        logger.info(f"项目导入成功到: {target_dir}")
        QMessageBox.information(self, self.tr("成功"),
                               self.tr("项目导入成功！"))

        # 刷新项目列表
        self.refresh_project_list()

    def _import_project_group(self, file_path):
        """导入项目组
        
        Args:
            file_path: 压缩文件路径
        """
        logger.info(f"开始导入项目组: {file_path}")

        target_dir = self.get_project_base_dir()

        # 解压文件
        if file_path.endswith('.zip'):
            self._extract_zip(file_path, target_dir)
        elif file_path.endswith('.tar.xz'):
            self._extract_tar_xz(file_path, target_dir)

        logger.info(f"项目组导入成功到: {target_dir}")
        QMessageBox.information(self, self.tr("成功"),
                               self.tr("项目组导入成功！"))

        # 刷新项目组列表
        self.refresh_project_group_list()

    def _extract_zip(self, file_path, target_dir):
        """解压ZIP文件
        
        Args:
            file_path: ZIP文件路径
            target_dir: 目标目录
        """
        import zipfile

        logger.debug(f"解压ZIP: {file_path} -> {target_dir}")

        with zipfile.ZipFile(file_path, 'r') as zipf:
            zipf.extractall(target_dir)

        logger.info(f"ZIP解压完成")

    def _extract_tar_xz(self, file_path, target_dir):
        """解压TAR.XZ文件
        
        Args:
            file_path: tar.xz文件路径
            target_dir: 目标目录
        """
        import tarfile

        logger.debug(f"解压TAR.XZ: {file_path} -> {target_dir}")

        with tarfile.open(file_path, 'r:xz') as tar:
            tar.extractall(target_dir)

        logger.info(f"TAR.XZ解压完成")

    def refresh_project_group_list(self):
        """刷新项目组列表"""
        logger.debug("刷新项目组列表")
        self.project_group_list.clear()

        project_base = self.get_project_base_dir()
        if not os.path.exists(project_base):
            os.makedirs(project_base)
            logger.debug(f"创建项目基础目录: {project_base}")

        # 获取所有项目组（基础目录下的子目录）
        groups = []
        try:
            for item in os.listdir(project_base):
                item_path = os.path.join(project_base, item)
                if os.path.isdir(item_path):
                    groups.append(item)
        except Exception as e:
            logger.error(f"读取项目组列表失败: {e}")

        # 如果没有项目组，创建默认项目组
        if not groups:
            default_group = self.tr("默认项目组")
            default_group_path = os.path.join(project_base, default_group)
            try:
                os.makedirs(default_group_path)
                groups.append(default_group)
                logger.info(f"创建默认项目组: {default_group}")
            except Exception as e:
                logger.error(f"创建默认项目组失败: {e}")

        # 添加项目组到列表
        self.project_group_list.addItem(self.tr("-- 选择项目组 --"), "")
        for group in sorted(groups):
            self.project_group_list.addItem(group, group)

        # 如果有当前项目组，选中它
        if hasattr(self, 'current_project_group') and self.current_project_group:
            index = self.project_group_list.findData(self.current_project_group)
            if index >= 0:
                self.project_group_list.setCurrentIndex(index)
                # 刷新项目列表
                self.refresh_project_list()

        logger.info(f"项目组列表刷新完成，共 {len(groups)} 个项目组")

    def on_project_group_selected(self, index):
        """项目组选择改变"""
        group_name = self.project_group_list.itemData(index)
        if group_name:
            self.switch_project_group(group_name)

    def switch_project_group(self, group_name):
        """切换到指定项目组"""
        logger.info(f"切换到项目组: {group_name}")
        self.current_project_group = group_name
        self.current_project_group_label.setText(group_name)

        # 保存当前项目组到设置
        self.settings.setValue("current_project_group", group_name)

        # 刷新项目列表
        self.refresh_project_list()

        logger.info(f"已切换到项目组: {group_name}")

    def create_new_project_group(self):
        """创建新项目组"""
        group_name = self.new_project_group_name.text().strip()

        if not group_name:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请输入项目组名称！"))
            return

        # 检查项目组名称是否合法
        import re
        if not re.match(r'^[\w\-\s]+$', group_name):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("项目组名称只能包含字母、数字、下划线、横线和空格！"))
            return

        project_base = self.get_project_base_dir()
        group_dir = os.path.join(project_base, group_name)

        # 检查组是否已存在
        if os.path.exists(group_dir):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr(f"项目组 '{group_name}' 已存在！"))
            return

        try:
            # 创建项目组目录
            os.makedirs(group_dir)

            logger.info(f"项目组创建成功: {group_name}")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目组 '{group_name}' 创建成功！"))

            # 清空输入框
            self.new_project_group_name.clear()

            # 刷新项目组列表并切换到新项目组
            self.refresh_project_group_list()
            index = self.project_group_list.findData(group_name)
            if index >= 0:
                self.project_group_list.setCurrentIndex(index)

        except Exception as e:
            logger.error(f"创建项目组失败: {e}")
            QMessageBox.critical(self, self.tr("错误"),
                               self.tr(f"创建项目组失败: {str(e)}"))

    def delete_project_group(self):
        """删除项目组"""
        group_name = self.project_group_list.currentData()

        if not group_name:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请先选择一个项目组！"))
            return

        # 确认删除
        reply = QMessageBox.question(self, self.tr("确认删除"),
                                    self.tr(f"确定要删除项目组 '{group_name}' 吗？\n")
                                    + self.tr("此操作将删除项目组下的所有项目，且不可恢复！"),
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        try:
            group_dir = os.path.join(self.get_project_base_dir(), group_name)
            import shutil
            shutil.rmtree(group_dir)

            logger.info(f"项目组删除成功: {group_name}")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目组 '{group_name}' 已删除！"))

            # 如果删除的是当前项目组，清除当前项目组
            if self.current_project_group == group_name:
                self.current_project_group = None
                self.current_project_group_label.setText(self.tr("未选择项目组"))
                self.settings.remove("current_project_group")
                # 同时清除当前项目
                self.current_project_name = None
                self.current_project_label.setText(self.tr("未选择项目"))
                self.settings.remove("current_project")

            # 刷新项目组列表
            self.refresh_project_group_list()

        except Exception as e:
            logger.error(f"删除项目组失败: {e}")
            QMessageBox.critical(self, self.tr("错误"),
                               self.tr(f"删除项目组失败: {str(e)}"))

    def refresh_project_list(self):
        """刷新项目列表"""
        logger.debug("刷新项目列表")
        self.project_list.clear()

        # 获取当前项目组目录
        if hasattr(self, 'current_project_group') and self.current_project_group:
            project_base = self.get_current_project_group_dir()
        else:
            project_base = self.get_project_base_dir()

        if not os.path.exists(project_base):
            os.makedirs(project_base)
            logger.debug(f"创建项目目录: {project_base}")

        # 获取所有项目目录（当前项目组下的子目录）
        projects = []
        try:
            for item in os.listdir(project_base):
                item_path = os.path.join(project_base, item)
                if os.path.isdir(item_path):
                    projects.append(item)
        except Exception as e:
            logger.error(f"读取项目列表失败: {e}")

        # 添加项目到列表
        self.project_list.addItem(self.tr("-- 选择项目 --"), "")
        for project in sorted(projects):
            self.project_list.addItem(project, project)

        # 如果有当前项目，选中它
        if hasattr(self, 'current_project_name') and self.current_project_name:
            index = self.project_list.findData(self.current_project_name)
            if index >= 0:
                self.project_list.setCurrentIndex(index)

        logger.info(f"项目列表刷新完成，共 {len(projects)} 个项目")

    def on_project_selected(self, index):
        """项目选择改变"""
        project_name = self.project_list.itemData(index)
        if project_name:
            self.switch_project(project_name)

    def switch_project(self, project_name):
        """切换到指定项目"""
        logger.info(f"切换到项目: {project_name}")
        self.current_project_name = project_name
        self.current_project_label.setText(project_name)

        # 更新项目路径显示
        project_dir = self.get_current_project_dir()
        if project_dir:
            self.project_path_label.setText(project_dir)

            # 自动加载项目资源（如果UI已初始化）
            self.load_project_resources(project_dir)

        # 保存当前项目到设置
        self.settings.setValue("current_project", project_name)

        logger.info(f"已切换到项目: {project_name}")

    def load_project_resources(self, project_dir):
        """自动加载项目中的资源文件"""
        if not project_dir or not os.path.exists(project_dir):
            logger.debug(f"项目目录不存在: {project_dir}")
            return

        logger.info(f"加载项目资源: {project_dir}")
        logger.debug(f"项目目录绝对路径: {os.path.abspath(project_dir)}")

        # 加载项目配置
        self.load_project_config(project_dir)

        assets_dir = os.path.join(project_dir, "Assets")
        affirmation_dir = os.path.join(assets_dir, "Affirmation")

        logger.debug(f"Assets目录: {assets_dir}, 是否存在: {os.path.exists(assets_dir)}")
        logger.debug(f"Affirmation目录: {affirmation_dir}, 是否存在: {os.path.exists(affirmation_dir)}")

        # 1. 加载 Raw.txt 文本文件
        if hasattr(self, 'text_file') and self.text_file is not None:
            raw_txt_path = os.path.join(affirmation_dir, "Raw.txt")
            logger.debug(f"查找文本文件: {raw_txt_path}, 是否存在: {os.path.exists(raw_txt_path)}")
            if os.path.exists(raw_txt_path):
                self.text_file.setText(raw_txt_path)
                self.text_sync.load_text_from_file(raw_txt_path)
                logger.info(f"自动加载文本文件: {raw_txt_path}")
            else:
                self.text_file.clear()
                self.current_text_file = None
                if hasattr(self, 'affirmation_text') and self.affirmation_text is not None:
                    self.affirmation_text.clear()

        # 2. 自动检测并加载肯定语音频文件（Affirmation 目录中的 .wav 或 .mp3 文件，排除 Raw.txt）
        if hasattr(self, 'affirmation_file') and self.affirmation_file is not None:
            affirmation_audio = self.find_first_audio_file(affirmation_dir)
            logger.debug(f"查找肯定语音频文件: {affirmation_audio}")
            if affirmation_audio:
                self.affirmation_file.setText(affirmation_audio)
                logger.info(f"自动加载肯定语音频: {affirmation_audio}")
                logger.debug(f"肯定语音频绝对路径: {os.path.abspath(affirmation_audio)}")
            else:
                self.affirmation_file.clear()

        # 3. 自动检测并加载背景音乐（Assets 目录中的 BGM.wav 或其他音频文件）
        if hasattr(self, 'background_file') and self.background_file is not None:
            bgm_path = os.path.join(assets_dir, "BGM.wav")
            logger.debug(f"查找背景音乐文件: {bgm_path}, 是否存在: {os.path.exists(bgm_path)}")
            if os.path.exists(bgm_path):
                self.background_file.setText(bgm_path)
                logger.info(f"自动加载背景音乐: {bgm_path}")
                logger.debug(f"背景音乐绝对路径: {os.path.abspath(bgm_path)}")
            else:
                # 尝试查找 Assets 目录中的其他音频文件
                bg_audio = self.find_first_audio_file(assets_dir, exclude_names=["Raw.txt"])
                logger.debug(f"查找其他背景音乐文件: {bg_audio}")
                if bg_audio and os.path.basename(bg_audio) != "Raw.txt":
                    self.background_file.setText(bg_audio)
                    logger.info(f"自动加载背景音乐: {bg_audio}")
                    logger.debug(f"背景音乐绝对路径: {os.path.abspath(bg_audio)}")
                else:
                    self.background_file.clear()

        # 4. 自动检测并加载视觉化图片（Assets 目录中的 Visualization.png 或其他图片文件）
        if hasattr(self, 'video_image') and self.video_image is not None:
            viz_path = os.path.join(assets_dir, "Visualization.png")
            logger.debug(f"查找视觉化图片: {viz_path}, 是否存在: {os.path.exists(viz_path)}")
            if os.path.exists(viz_path):
                self.video_image.setText(viz_path)
                logger.info(f"自动加载视觉化图片: {viz_path}")
                logger.debug(f"视觉化图片绝对路径: {os.path.abspath(viz_path)}")
            else:
                # 尝试查找 Assets 目录中的其他图片文件
                image_file = self.find_first_image_file(assets_dir)
                logger.debug(f"查找其他视觉化图片: {image_file}")
                if image_file:
                    self.video_image.setText(image_file)
                    logger.info(f"自动加载视觉化图片: {image_file}")
                    logger.debug(f"视觉化图片绝对路径: {os.path.abspath(image_file)}")
                else:
                    self.video_image.clear()

    def find_first_audio_file(self, directory, exclude_names=None):
        """查找目录中的第一个音频文件"""
        if not directory or not os.path.exists(directory):
            return None

        exclude_names = exclude_names or []
        audio_extensions = ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma']

        try:
            for filename in os.listdir(directory):
                if filename in exclude_names:
                    continue
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in audio_extensions:
                        return file_path
        except Exception as e:
            logger.error(f"查找音频文件失败: {directory}, 错误: {e}")

        return None

    def find_first_image_file(self, directory):
        """查找目录中的第一个图片文件"""
        if not directory or not os.path.exists(directory):
            return None

        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif']

        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in image_extensions:
                        return file_path
        except Exception as e:
            logger.error(f"查找图片文件失败: {directory}, 错误: {e}")

        return None

    def create_project(self):
        """创建新项目"""
        project_name = self.new_project_name.text().strip()

        if not project_name:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请输入项目名称！"))
            return

        # 检查项目名称是否合法
        import re
        if not re.match(r'^[\w\-\s]+$', project_name):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("项目名称只能包含字母、数字、下划线、横线和空格！"))
            return

        # 获取项目基础目录（支持项目组）
        if hasattr(self, 'current_project_group') and self.current_project_group:
            project_base = self.get_current_project_group_dir()
        else:
            project_base = self.get_project_base_dir()
        project_dir = os.path.join(project_base, project_name)

        # 检查项目是否已存在
        if os.path.exists(project_dir):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr(f"项目 '{project_name}' 已存在！"))
            return

        # 检查是否选择了项目组
        if not hasattr(self, 'current_project_group') or not self.current_project_group:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请先选择一个项目组！"))
            return

        try:
            # 创建项目目录结构
            os.makedirs(project_dir)
            os.makedirs(os.path.join(project_dir, "Assets", "Affirmation"))
            os.makedirs(os.path.join(project_dir, "Releases", "Audio"))
            os.makedirs(os.path.join(project_dir, "Releases", "Video"))

            # 创建 README.md
            readme_path = os.path.join(project_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# {project_name}\n\n")
                f.write(self.tr("项目描述\n\n"))
                f.write(self.tr("## 肯定语\n\n"))
                f.write(self.tr("在此添加肯定语描述...\n\n"))
                f.write(self.tr("## 背景音乐\n\n"))
                f.write(self.tr("在此添加背景音乐描述...\n\n"))

            # 创建 Raw.txt
            raw_path = os.path.join(project_dir, "Assets", "Affirmation", "Raw.txt")
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(self.tr("# 在此输入肯定语文本\n"))

            # 创建默认配置文件
            config_path = os.path.join(project_dir, "config.json")
            default_config = {
                "version": "1.0",
                "metadata": {
                    "title": "",
                    "author": ""
                }
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.debug(f"创建默认配置文件: {config_path}")

            logger.info(f"项目创建成功: {project_name}")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目 '{project_name}' 创建成功！"))

            # 清空输入框
            self.new_project_name.clear()

            # 刷新项目列表并切换到新项目
            self.refresh_project_list()
            index = self.project_list.findData(project_name)
            if index >= 0:
                self.project_list.setCurrentIndex(index)

        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            QMessageBox.critical(self, self.tr("错误"),
                               self.tr(f"创建项目失败: {str(e)}"))

    def delete_project(self):
        """删除项目"""
        project_name = self.project_list.currentData()

        if not project_name:
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("请先选择一个项目！"))
            return

        # 确认删除
        reply = QMessageBox.question(self, self.tr("确认删除"),
                                    self.tr(f"确定要删除项目 '{project_name}' 吗？\n")
                                    + self.tr("此操作不可恢复！"),
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        try:
            # 获取项目目录（支持项目组）
            if hasattr(self, 'current_project_group') and self.current_project_group:
                project_base = self.get_current_project_group_dir()
            else:
                project_base = self.get_project_base_dir()
            project_dir = os.path.join(project_base, project_name)
            import shutil
            shutil.rmtree(project_dir)

            logger.info(f"项目删除成功: {project_name}")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目 '{project_name}' 已删除！"))

            # 如果删除的是当前项目，清除当前项目
            if self.current_project_name == project_name:
                self.current_project_name = None
                self.current_project_label.setText(self.tr("未选择项目"))
                self.project_path_label.setText("./Project/")
                self.settings.remove("current_project")

            # 刷新项目列表
            self.refresh_project_list()

        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            QMessageBox.critical(self, self.tr("错误"),
                               self.tr(f"删除项目失败: {str(e)}"))