from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFileDialog, QScrollArea, QMessageBox, QTabWidget, QProgressDialog)
from PyQt5.QtCore import Qt, QTranslator, QSettings
import os
import subprocess
import sys
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .AudioRecorder import AudioRecorder
from .AudioManager import AudioManager
from .RecordingManager import RecordingManager
from .PreviewManager import PreviewManager
from .TTSManager import TTSManager
from .OutputManager import OutputManager
from .LogHandler import LogHandler
from .TextFileSync import TextFileSync
from .ProjectManager import ProjectManager
from .ReleaseManager import ReleaseManager
from .UIFactory import UIFactory
from .BatchProcessor import BatchProcessorDialog

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
        # 确保字符串类型（PyQt5可能返回QByteArray）
        if isinstance(self.current_project_group, bytes):
            self.current_project_group = self.current_project_group.decode('utf-8')
        if isinstance(self.current_project_name, bytes):
            self.current_project_name = self.current_project_name.decode('utf-8')
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

        # 初始化管理器（需要在initUI之前创建）
        self.audio_manager = AudioManager(self)
        self.recording_manager = RecordingManager(self)
        self.tts_manager = TTSManager(self)
        self.output_manager = OutputManager(self)
        self.project_manager = ProjectManager(self)
        self.preview_manager = PreviewManager(self)
        self.release_manager = ReleaseManager(self)

        # 初始化文本文件同步处理器（需要在ui_factory之前）
        self.text_sync = TextFileSync(self)

        # 初始化日志处理器（需要在ui_factory之前）
        self.log_handler = LogHandler(self)

        self.ui_factory = UIFactory(self)
        
        self.initUI()
        self.setupTranslations()

        # 枚举设备
        self.audio_manager.enumerate_tts_engines()
        self.audio_manager.enumerate_audio_devices()

        # 设置文本同步
        self.text_sync.setup_text_file_sync()

        # 设置日志处理器
        self.log_handler.setup_log_handler()

        # UI初始化完成后，自动加载项目资源
        # 注意：项目资源会在project_manager.refresh_project_group_list()中自动加载
        # 该函数在initUI()的最后被调用，确保所有UI组件（包括output_list）已创建

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

        # 禁用元数据组
        if hasattr(self, 'metadata_group'):
            self.metadata_group.setEnabled(False)
            self.metadata_group.setToolTip(self.tr("需要安装ffmpeg才能使用元数据功能"))

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
            if hasattr(self, 'release_tab_index'):
                self.tab_widget.setTabText(self.release_tab_index, self.tr("输出管理"))
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
            # 项目组区域
            if hasattr(self, 'project_group_section'):
                self.project_group_section.setTitle(self.tr("项目组"))
                self.label_current_project_group.setText(self.tr("当前:"))
                if not hasattr(self, 'current_project_group') or not self.current_project_group:
                    self.current_project_group_label.setText(self.tr("未选择项目组"))
                self.label_project_group_list.setText(self.tr("切换:"))
                self.project_group_list.setToolTip(self.tr("选择或切换当前项目组"))
                self.label_new_project_group.setText(self.tr("新建:"))
                if hasattr(self, 'new_project_group_name'):
                    self.new_project_group_name.setToolTip(self.tr("输入新项目组名称"))
                    self.new_project_group_name.setPlaceholderText(self.tr("项目组名称"))
                self.create_project_group_btn.setText(self.tr("创建"))
                self.create_project_group_btn.setToolTip(self.tr("创建新项目组"))
                self.delete_project_group_btn.setText(self.tr("删除项目组"))
                self.delete_project_group_btn.setToolTip(self.tr("删除选中的项目组"))
            # 项目区域
            if hasattr(self, 'project_section'):
                self.project_section.setTitle(self.tr("项目"))
                self.label_current_project.setText(self.tr("当前:"))
                if not hasattr(self, 'current_project_name') or not self.current_project_name:
                    self.current_project_label.setText(self.tr("未选择项目"))
                self.label_project_list.setText(self.tr("切换:"))
                self.project_list.setToolTip(self.tr("选择或切换当前项目"))
                self.refresh_projects_btn.setText(self.tr("刷新"))
                self.refresh_projects_btn.setToolTip(self.tr("刷新项目列表"))
                self.label_new_project.setText(self.tr("新建:"))
                if hasattr(self, 'new_project_name'):
                    self.new_project_name.setToolTip(self.tr("输入新项目名称"))
                    self.new_project_name.setPlaceholderText(self.tr("项目名称"))
                self.create_project_btn.setText(self.tr("创建"))
                self.create_project_btn.setToolTip(self.tr("创建新项目"))
                # 项目操作按钮
                if hasattr(self, 'copy_project_btn'):
                    self.copy_project_btn.setText(self.tr("复制"))
                    self.copy_project_btn.setToolTip(self.tr("复制项目到当前项目组"))
                if hasattr(self, 'cut_project_btn'):
                    self.cut_project_btn.setText(self.tr("剪切"))
                    self.cut_project_btn.setToolTip(self.tr("剪切项目到其他项目组"))
                self.delete_project_btn.setText(self.tr("删除"))
                self.delete_project_btn.setToolTip(self.tr("删除选中的项目"))
                self.label_project_path.setText(self.tr("路径:"))
            # 导入导出区域
            if hasattr(self, 'import_export_section'):
                self.import_export_section.setTitle(self.tr("导入/导出"))
                self.export_project_btn.setText(self.tr("导出项目"))
                self.export_project_btn.setToolTip(self.tr("将当前项目导出为压缩文件"))
                self.export_project_group_btn.setText(self.tr("导出项目组"))
                self.export_project_group_btn.setToolTip(self.tr("将当前项目组导出为压缩文件"))
                self.import_btn.setText(self.tr("导入"))
                self.import_btn.setToolTip(self.tr("从压缩文件导入项目或项目组"))
            # 批量处理区域
            if hasattr(self, 'batch_section'):
                self.batch_section.setTitle(self.tr("批量处理"))
                self.batch_generate_btn.setText(self.tr("批量生成"))
                self.batch_generate_btn.setToolTip(self.tr("批量生成选中的项目/项目组"))
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
        project_layout.addWidget(self.ui_factory.create_project_group())

        affirmation_widget = QWidget()
        affirmation_layout = QVBoxLayout(affirmation_widget)
        affirmation_layout.addWidget(self.ui_factory.create_affirmation_group())

        background_widget = QWidget()
        background_layout = QVBoxLayout(background_widget)
        background_layout.addWidget(self.ui_factory.create_background_group())

        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.addWidget(self.ui_factory.create_output_group())

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.addWidget(self.ui_factory.create_settings_group())

        # 创建特定频率音轨选项卡内容
        freq_track_widget = QWidget()
        freq_track_layout = QVBoxLayout(freq_track_widget)
        freq_track_layout.addWidget(self.ui_factory.create_freq_track_group())

        # 创建日志选项卡内容
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.addWidget(self.ui_factory.create_log_group())

        # 创建输出文件管理选项卡内容
        release_widget = QWidget()
        release_layout = QVBoxLayout(release_widget)
        release_layout.addWidget(self.ui_factory.create_release_group())

        # 添加选项卡
        self.project_tab_index = self.tab_widget.addTab(project_widget, self.tr("项目"))
        self.affirmation_tab_index = self.tab_widget.addTab(affirmation_widget, self.tr("肯定语"))
        self.background_tab_index = self.tab_widget.addTab(background_widget, self.tr("背景音"))
        self.freq_track_tab_index = self.tab_widget.addTab(freq_track_widget, self.tr("特定频率音轨"))
        self.output_tab_index = self.tab_widget.addTab(output_widget, self.tr("输出"))
        self.release_tab_index = self.tab_widget.addTab(release_widget, self.tr("输出管理"))
        self.settings_tab_index = self.tab_widget.addTab(settings_widget, self.tr("设置"))
        self.log_tab_index = self.tab_widget.addTab(log_widget, self.tr("日志"))

        # 连接选项卡切换信号，用于刷新输出列表
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        # 根据ffmpeg可用性更新UI
        self.update_ui_for_ffmpeg_availability()

        # 所有UI组件创建完成后，刷新项目列表
        # 这必须在所有UI组件（包括output_list）创建完成后调用
        self.project_manager.refresh_project_group_list()

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

    def update_progress(self, value):
        """更新进度"""
        self.output_manager.update_progress(value)

    def cancel_generation(self):
        """取消生成"""
        self.output_manager.cancel_generation()

    def on_generation_finished(self, output_path):
        """生成完成回调"""
        self.output_manager.on_generation_finished(output_path)

    def on_video_finished(self, output_path):
        """视频生成完成回调"""
        self.output_manager.on_video_finished(output_path)

    def on_generation_error(self, error_msg):
        """生成错误回调"""
        self.output_manager.on_generation_error(error_msg)

    def on_tab_changed(self, index):
        """选项卡切换回调"""
        # 如果切换到输出管理选项卡，刷新输出列表
        if hasattr(self, 'release_tab_index') and index == self.release_tab_index:
            if (hasattr(self, 'release_manager') and self.release_manager and
                self.release_manager.output_list is not None):
                self.release_manager.refresh_output_list()

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

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("导出项目"),
            f"{self.current_project_name}.zip",
            self.tr("ZIP 文件 (*.zip);;TAR.XZ 文件 (*.tar.xz)")
        )

        if not file_path:
            return

        if "tar.xz" in selected_filter.lower() or file_path.endswith('.tar.xz'):
            if not file_path.endswith('.tar.xz'):
                file_path += '.tar.xz'
        else:
            if not file_path.endswith('.zip'):
                file_path += '.zip'

        # 创建进度对话框
        progress_dialog = QProgressDialog(
            self.tr("正在导出项目..."),
            self.tr("取消"),
            0, 100, self
        )
        progress_dialog.setWindowTitle(self.tr("导出进度"))
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)

        # 创建导出工作线程
        from .ProjectManager import ExportWorker
        self.export_worker = ExportWorker(project_dir, file_path, "project")
        
        # 连接信号
        self.export_worker.progress_updated.connect(progress_dialog.setValue)
        self.export_worker.file_processed.connect(
            lambda f: progress_dialog.setLabelText(self.tr(f"正在导出: {f}"))
        )
        
        def on_export_finished(success, message):
            progress_dialog.close()
            if success:
                logger.info(f"项目导出成功: {message}")
                QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目 '{self.current_project_name}' 导出成功！\n保存位置: {message}"))
            else:
                if message != "导出已取消":
                    logger.error(f"导出项目失败: {message}")
                    QMessageBox.critical(self, self.tr("错误"),
                                       self.tr(f"导出项目失败: {message}"))
        
        self.export_worker.export_finished.connect(on_export_finished)
        progress_dialog.canceled.connect(self.export_worker.cancel)
        
        # 启动导出
        self.export_worker.start()

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

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("导出项目组"),
            f"{self.current_project_group}.zip",
            self.tr("ZIP 文件 (*.zip);;TAR.XZ 文件 (*.tar.xz)")
        )

        if not file_path:
            return

        if "tar.xz" in selected_filter.lower() or file_path.endswith('.tar.xz'):
            if not file_path.endswith('.tar.xz'):
                file_path += '.tar.xz'
        else:
            if not file_path.endswith('.zip'):
                file_path += '.zip'

        # 创建进度对话框
        progress_dialog = QProgressDialog(
            self.tr("正在导出项目组..."),
            self.tr("取消"),
            0, 100, self
        )
        progress_dialog.setWindowTitle(self.tr("导出进度"))
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)

        # 创建导出工作线程
        from .ProjectManager import ExportWorker
        self.export_worker = ExportWorker(group_dir, file_path, "group")
        
        # 连接信号
        self.export_worker.progress_updated.connect(progress_dialog.setValue)
        self.export_worker.file_processed.connect(
            lambda f: progress_dialog.setLabelText(self.tr(f"正在导出: {f}"))
        )
        
        def on_export_finished(success, message):
            progress_dialog.close()
            if success:
                logger.info(f"项目组导出成功: {message}")
                QMessageBox.information(self, self.tr("成功"),
                                   self.tr(f"项目组 '{self.current_project_group}' 导出成功！\n保存位置: {message}"))
            else:
                if message != "导出已取消":
                    logger.error(f"导出项目组失败: {message}")
                    QMessageBox.critical(self, self.tr("错误"),
                                       self.tr(f"导出项目组失败: {message}"))
        
        self.export_worker.export_finished.connect(on_export_finished)
        progress_dialog.canceled.connect(self.export_worker.cancel)
        
        # 启动导出
        self.export_worker.start()

    def import_project_or_group(self):
        """导入项目或项目组"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("导入项目/项目组"),
            "",
            self.tr("压缩文件 (*.zip *.tar.xz)")
        )

        if not file_path:
            return

        self.project_manager.import_project_or_group(file_path)

    def change_language(self, index):
        """语言选择改变"""
        self.new_language = self.language_combo.itemData(index)
        logger.debug(f"语言选择改变: {self.new_language}")
    
    def apply_language_settings(self):
        """应用语言设置"""
        logger.info("开始应用语言设置")
        
        if hasattr(self, 'new_language') and self.new_language:
            logger.info(f"应用新语言设置: {self.new_language}")
            
            self.settings.setValue("language", self.new_language)
            self.current_language = self.new_language
            
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
            self.settings.clear()
            logger.debug("设置已清空")
            
            self.current_language = "zh_CN"
            self.settings.setValue("language", self.current_language)
            logger.info(f"语言重置为默认: {self.current_language}")
            
            self.setupTranslations()
            
            current_index = self.language_combo.findData(self.current_language)
            if current_index >= 0:
                self.language_combo.setCurrentIndex(current_index)
            
            logger.info("设置重置完成")
            QMessageBox.information(self, self.tr("成功"),
                                   self.tr("所有设置已重置为默认值。"))

    def clear_log_display(self):
        """清空日志显示区域"""
        if hasattr(self, 'log_text_edit'):
            self.log_text_edit.clear()
            logger.info("日志显示区域已清空")

    def open_batch_processor(self):
        """打开批量处理对话框"""
        logger.info("打开批量处理对话框")
        dialog = BatchProcessorDialog(self, self.project_manager, self.output_manager)
        dialog.exec_()