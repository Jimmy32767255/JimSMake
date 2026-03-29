from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QSlider, QCheckBox, QFileDialog, QSpinBox, QDoubleSpinBox,
                             QScrollArea, QGridLayout, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, QTranslator, QSettings, QThread, pyqtSignal
import pyttsx3
import pyaudio
import wave
import os
from loguru import logger


class AudioRecorder(QThread):
    """音频录制线程"""
    recording_finished = pyqtSignal(str)
    recording_error = pyqtSignal(str)
    
    def __init__(self, device_index=None, sample_rate=44100, channels=1):
        super().__init__()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16
        self.is_recording = False
        self.frames = []
        self.output_file = None
        
    def set_output_file(self, file_path):
        """设置输出文件路径"""
        self.output_file = file_path
        
    def run(self):
        """开始录制"""
        try:
            self.frames = []
            self.is_recording = True
            
            p = pyaudio.PyAudio()
            
            # 打开音频流
            stream = p.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("开始录制音频")
            
            while self.is_recording:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception as e:
                    logger.error(f"读取音频数据时出错: {e}")
                    break
            
            # 停止并关闭音频流
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # 保存音频文件
            if self.output_file and self.frames:
                self._save_audio()
                self.recording_finished.emit(self.output_file)
            
        except Exception as e:
            logger.error(f"录音过程中出错: {e}")
            self.recording_error.emit(str(e))
    
    def _save_audio(self):
        """保存录制的音频到文件"""
        try:
            wf = wave.open(self.output_file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            logger.info(f"音频文件已保存: {self.output_file}")
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            raise
    
    def stop(self):
        """停止录制"""
        self.is_recording = False
        logger.info("停止录制音频")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("初始化主窗口")
        
        # 初始化设置
        self.settings = QSettings("JimSMake", "SMake")
        self.current_language = self.settings.value("language", "zh_CN")
        self.current_project_name = self.settings.value("current_project", "")
        logger.info(f"加载设置，当前语言: {self.current_language}, 当前项目: {self.current_project_name}")

        # 初始化录音相关变量
        self.recorder = None
        self.is_recording = False

        self.initUI()
        self.setupTranslations()
        self.enumerate_tts_engines()
        self.enumerate_audio_devices()
        
        logger.info("主窗口初始化完成")
        
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
        translation_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Translation")
        logger.debug(f"翻译文件目录: {translation_dir}")
        
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
            if hasattr(self, 'output_tab_index'):
                self.tab_widget.setTabText(self.output_tab_index, self.tr("输出"))
            if hasattr(self, 'settings_tab_index'):
                self.tab_widget.setTabText(self.settings_tab_index, self.tr("设置"))
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

        # 更新背景音组
        if hasattr(self, 'background_group'):
            self.background_group.setTitle(self.tr("背景音"))
            self.label_bg_file.setText(self.tr("背景音文件:"))
            self.background_file.setToolTip(self.tr("选择一个音频文件作为背景音。"))
            self.btn_browse_bg.setText(self.tr("浏览..."))
            self.btn_browse_bg.setToolTip(self.tr("选择背景音频文件"))
            self.label_bg_volume.setText(self.tr("音量:"))
            self.background_volume.setToolTip(self.tr("改变背景音音轨的音量。（单位为分贝）"))

        # 更新输出组
        if hasattr(self, 'output_group'):
            self.output_group.setTitle(self.tr("输出"))
            self.generate_audio.setText(self.tr("生成音频"))
            self.generate_audio.setToolTip(self.tr("是否生成音频。"))
            self.audio_group.setTitle(self.tr("音频设置"))
            self.label_audio_format.setText(self.tr("格式:"))
            self.label_audio_sample_rate.setText(self.tr("采样率:"))
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

        # 更新设置组
        if hasattr(self, 'settings_group'):
            self.settings_group.setTitle(self.tr("设置"))
            self.label_language.setText(self.tr("语言:"))
            self.apply_language_btn.setText(self.tr("应用语言"))
            self.reset_settings_btn.setText(self.tr("重置设置"))
            self.about_group.setTitle(self.tr("关于"))
            self.about_label.setText(self.tr("SMake"))

        # 更新项目组
        if hasattr(self, 'project_group'):
            self.project_group.setTitle(self.tr("项目管理"))
            self.label_current_project.setText(self.tr("当前项目:"))
            if not hasattr(self, 'current_project_name') or not self.current_project_name:
                self.current_project_label.setText(self.tr("未选择项目"))
            self.label_project_list.setText(self.tr("项目列表:"))
            self.project_list.setToolTip(self.tr("选择或切换当前项目"))
            self.refresh_projects_btn.setText(self.tr("刷新"))
            self.refresh_projects_btn.setToolTip(self.tr("刷新项目列表"))
            self.label_new_project.setText(self.tr("新建项目:"))
            self.new_project_name.setToolTip(self.tr("输入新项目名称"))
            self.new_project_name.setPlaceholderText(self.tr("输入项目名称"))
            self.create_project_btn.setText(self.tr("创建项目"))
            self.create_project_btn.setToolTip(self.tr("创建新项目"))
            self.delete_project_btn.setText(self.tr("删除项目"))
            self.delete_project_btn.setToolTip(self.tr("删除选中的项目"))
            self.label_project_path.setText(self.tr("项目路径:"))
            self.project_structure_group.setTitle(self.tr("项目结构"))
            self.project_structure_label.setText(
                self.tr("项目名称/\n"
                       "  ├── README.md (项目描述)\n"
                       "  ├── Assets/ (资产)\n"
                       "  │   ├── BGM.wav (背景音乐)\n"
                       "  │   ├── Visualization.png (视觉化图片)\n"
                       "  │   └── Affirmation/ (肯定语)\n"
                       "  │       ├── *.wav (肯定语音频)\n"
                       "  │       └── Raw.txt (肯定语文本)\n"
                       "  └── Releases/ (发行版)\n"
                       "      ├── Audio/ (音频输出)\n"
                       "      └── Video/ (视频输出)")
            )

        logger.info("UI文本重新翻译完成")

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
            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)
                
                # 只显示输入设备（麦克风）
                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name']
                    # 清理设备名称中的特殊字符
                    device_name = device_name.strip()
                    
                    # 添加设备到下拉列表
                    self.record_device.addItem(device_name)
                    input_devices.append(device_name)
                    logger.debug(f"添加音频输入设备: {device_name}")
            
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

        # 添加选项卡
        self.project_tab_index = self.tab_widget.addTab(project_widget, self.tr("项目"))
        self.affirmation_tab_index = self.tab_widget.addTab(affirmation_widget, self.tr("肯定语"))
        self.background_tab_index = self.tab_widget.addTab(background_widget, self.tr("背景音"))
        self.output_tab_index = self.tab_widget.addTab(output_widget, self.tr("输出"))
        self.settings_tab_index = self.tab_widget.addTab(settings_widget, self.tr("设置"))
        
        main_layout.addWidget(self.tab_widget)
        
    def create_project_group(self):
        """创建项目组"""
        self.project_group = QGroupBox(self.tr("项目管理"))
        layout = QGridLayout()

        # 当前项目显示
        self.label_current_project = QLabel(self.tr("当前项目:"))
        layout.addWidget(self.label_current_project, 0, 0)
        self.current_project_label = QLabel(self.tr("未选择项目"))
        self.current_project_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addWidget(self.current_project_label, 0, 1, 1, 2)

        # 项目列表
        self.label_project_list = QLabel(self.tr("项目列表:"))
        layout.addWidget(self.label_project_list, 1, 0)
        self.project_list = QComboBox()
        self.project_list.setToolTip(self.tr("选择或切换当前项目"))
        self.project_list.currentIndexChanged.connect(self.on_project_selected)
        layout.addWidget(self.project_list, 1, 1, 1, 2)

        # 刷新项目列表按钮
        self.refresh_projects_btn = QPushButton(self.tr("刷新"))
        self.refresh_projects_btn.setToolTip(self.tr("刷新项目列表"))
        self.refresh_projects_btn.clicked.connect(self.refresh_project_list)
        layout.addWidget(self.refresh_projects_btn, 2, 0)

        # 新建项目
        self.label_new_project = QLabel(self.tr("新建项目:"))
        layout.addWidget(self.label_new_project, 3, 0)
        self.new_project_name = QLineEdit()
        self.new_project_name.setToolTip(self.tr("输入新项目名称"))
        self.new_project_name.setPlaceholderText(self.tr("输入项目名称"))
        layout.addWidget(self.new_project_name, 3, 1)

        self.create_project_btn = QPushButton(self.tr("创建项目"))
        self.create_project_btn.setToolTip(self.tr("创建新项目"))
        self.create_project_btn.clicked.connect(self.create_project)
        layout.addWidget(self.create_project_btn, 3, 2)

        # 删除项目按钮
        self.delete_project_btn = QPushButton(self.tr("删除项目"))
        self.delete_project_btn.setToolTip(self.tr("删除选中的项目"))
        self.delete_project_btn.clicked.connect(self.delete_project)
        layout.addWidget(self.delete_project_btn, 4, 0, 1, 3)

        # 项目路径信息
        self.label_project_path = QLabel(self.tr("项目路径:"))
        layout.addWidget(self.label_project_path, 5, 0)
        self.project_path_label = QLabel("./Project/")
        self.project_path_label.setStyleSheet("color: gray;")
        self.project_path_label.setWordWrap(True)
        layout.addWidget(self.project_path_label, 5, 1, 1, 2)

        # 项目结构说明
        self.project_structure_group = QGroupBox(self.tr("项目结构"))
        structure_layout = QVBoxLayout()
        self.project_structure_label = QLabel(
            self.tr("项目名称/\n"
                   "  ├── README.md (项目描述)\n"
                   "  ├── Assets/ (资产)\n"
                   "  │   ├── BGM.wav (背景音乐)\n"
                   "  │   ├── Visualization.png (视觉化图片)\n"
                   "  │   └── Affirmation/ (肯定语)\n"
                   "  │       ├── *.wav (肯定语音频)\n"
                   "  │       └── Raw.txt (肯定语文本)\n"
                   "  └── Releases/ (发行版)\n"
                   "      ├── Audio/ (音频输出)\n"
                   "      └── Video/ (视频输出)")
        )
        self.project_structure_label.setStyleSheet("font-family: monospace; color: #666;")
        structure_layout.addWidget(self.project_structure_label)
        self.project_structure_group.setLayout(structure_layout)
        layout.addWidget(self.project_structure_group, 6, 0, 1, 3)

        self.project_group.setLayout(layout)

        # 初始化时刷新项目列表
        self.refresh_project_list()

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
        self.affirmation_volume.setValue(-240)
        self.affirmation_volume.setToolTip(self.tr("改变肯定语音轨的音量。（单位为分贝）"))
        layout.addWidget(self.affirmation_volume, 5, 1)

        self.affirmation_volume_spin = QDoubleSpinBox()
        self.affirmation_volume_spin.setRange(-60.0, 0.0)
        self.affirmation_volume_spin.setValue(0.0)
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
        self.background_volume_spin.setValue(-30.0)
        self.background_volume_spin.setSingleStep(0.5)
        self.background_volume_spin.valueChanged.connect(
            lambda v: self.background_volume.setValue(int(v * 10)))
        self.background_volume.valueChanged.connect(
            lambda v: self.background_volume_spin.setValue(v / 10.0))
        layout.addWidget(self.background_volume_spin, 1, 2)

        self.background_group.setLayout(layout)
        return self.background_group
    
    def create_output_group(self):
        """创建输出组"""
        self.output_group = QGroupBox(self.tr("输出"))
        layout = QGridLayout()

        row = 0

        # 生成音频复选框
        self.generate_audio = QCheckBox(self.tr("生成音频"))
        self.generate_audio.setChecked(True)
        self.generate_audio.setToolTip(self.tr("是否生成音频。"))
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

        # 生成视频复选框
        self.generate_video = QCheckBox(self.tr("生成视频"))
        self.generate_video.setToolTip(self.tr("是否生成视频。"))
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

        # 生成按钮
        self.generate_btn = QPushButton(self.tr("生成项目"))
        self.generate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-size: 14pt; padding: 10px; }")
        self.generate_btn.setToolTip(self.tr("开始生成项目！"))
        self.generate_btn.clicked.connect(self.generate_project)
        layout.addWidget(self.generate_btn, row, 0, 1, 3)

        self.output_group.setLayout(layout)
        return self.output_group

# ---以上为界面部分，使用QtDesigner时请将生成的代码粘贴覆盖到上方，本界面相关逻辑即将在下方实现。---

    def browse_file(self, line_edit, file_filter):
        """浏览文件对话框"""
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("选择文件"), "", file_filter)
        if file_path:
            line_edit.setText(file_path)

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
            device_name = self.record_device.currentText()
            device_index = None

            # 如果不是系统默认，查找设备索引
            if device_name != self.tr("系统默认"):
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

    def generate_project(self):
        """生成项目"""
        # 验证至少选择了一项
        if not self.generate_audio.isChecked() and not self.generate_video.isChecked():
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("必须至少选择生成音频或生成视频一项！"))
            return

        # 验证必要文件
        if self.generate_audio.isChecked() and not self.affirmation_file.text():
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr("生成音频需要选择肯定语音频文件！"))
            return

        QMessageBox.information(self, self.tr("成功"),
                               self.tr("项目生成功能尚未实现，此版本为界面演示。"))
    
    def create_settings_group(self):
        """创建设置组"""
        self.settings_group = QGroupBox(self.tr("设置"))
        layout = QGridLayout()

        # 语言设置
        self.label_language = QLabel(self.tr("语言:"))
        layout.addWidget(self.label_language, 0, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("English", "en_US")

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

    # ==================== 项目管理方法 ====================

    def get_project_base_dir(self):
        """获取项目基础目录"""
        return os.path.join(os.path.dirname(__file__), "..", "..", "Project")

    def get_current_project_dir(self):
        """获取当前项目目录"""
        if hasattr(self, 'current_project_name') and self.current_project_name:
            return os.path.join(self.get_project_base_dir(), self.current_project_name)
        return None

    def refresh_project_list(self):
        """刷新项目列表"""
        logger.debug("刷新项目列表")
        self.project_list.clear()

        project_base = self.get_project_base_dir()
        if not os.path.exists(project_base):
            os.makedirs(project_base)
            logger.debug(f"创建项目基础目录: {project_base}")

        # 获取所有项目目录
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

        # 保存当前项目到设置
        self.settings.setValue("current_project", project_name)

        logger.info(f"已切换到项目: {project_name}")

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

        project_base = self.get_project_base_dir()
        project_dir = os.path.join(project_base, project_name)

        # 检查项目是否已存在
        if os.path.exists(project_dir):
            QMessageBox.warning(self, self.tr("警告"),
                               self.tr(f"项目 '{project_name}' 已存在！"))
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
            project_dir = os.path.join(self.get_project_base_dir(), project_name)
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