from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QSlider, QCheckBox, QFileDialog, QSpinBox, QDoubleSpinBox,
                             QScrollArea, QGridLayout, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, QTranslator, QLocale
from PyQt5.QtGui import QDoubleValidator
import pyttsx3
import pyaudio

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupTranslations()
        self.enumerate_tts_engines()
        self.enumerate_audio_devices()
        
    def setupTranslations(self):
        """设置翻译支持"""
        # 这里可以加载翻译文件
        # self.translator = QTranslator()
        # self.translator.load("smake_zh_CN.qm")
        # QApplication.instance().installTranslator(self.translator)
        pass
        
    def enumerate_tts_engines(self):
        """枚举系统中已安装的TTS引擎"""
        try:
            # 清空现有选项
            self.tts_engine.clear()
            
            # 添加默认选项
            self.tts_engine.addItem(self.tr("系统默认"))
            
            # 使用pyttsx3枚举TTS引擎
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
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
            
            # 释放引擎资源
            engine.stop()
            
        except Exception as e:
            # 如果枚举失败，保留默认选项
            print(f"TTS引擎枚举失败: {e}")
            self.tts_engine.clear()
            self.tts_engine.addItem(self.tr("系统默认"))
            self.tts_engine.addItem("Microsoft")
            self.tts_engine.addItem("Google")
    
    def enumerate_audio_devices(self):
        """枚举系统中可用的音频输入设备"""
        try:
            # 清空现有选项
            self.record_device.clear()
            
            # 添加默认选项
            self.record_device.addItem(self.tr("系统默认"))
            
            # 使用pyaudio枚举音频设备
            p = pyaudio.PyAudio()
            
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                
                # 只显示输入设备（麦克风）
                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name']
                    # 清理设备名称中的特殊字符
                    device_name = device_name.strip()
                    
                    # 添加设备到下拉列表
                    self.record_device.addItem(device_name)
            
            # 释放pyaudio资源
            p.terminate()
            
        except Exception as e:
            # 如果枚举失败，保留默认选项
            print(f"音频设备枚举失败: {e}")
            self.record_device.clear()
            self.record_device.addItem(self.tr("系统默认"))
            self.record_device.addItem(self.tr("麦克风 (Realtek)"))
        
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
        affirmation_widget = QWidget()
        affirmation_layout = QVBoxLayout(affirmation_widget)
        affirmation_layout.addWidget(self.create_affirmation_group())
        
        background_widget = QWidget()
        background_layout = QVBoxLayout(background_widget)
        background_layout.addWidget(self.create_background_group())
        
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.addWidget(self.create_output_group())
        
        # 添加选项卡
        self.tab_widget.addTab(affirmation_widget, self.tr("肯定语"))
        self.tab_widget.addTab(background_widget, self.tr("背景音"))
        self.tab_widget.addTab(output_widget, self.tr("输出"))
        
        main_layout.addWidget(self.tab_widget)
        
    def create_affirmation_group(self):
        """创建肯定语组"""
        group_box = QGroupBox(self.tr("肯定语"))
        layout = QGridLayout()
        
        # 文件选择
        layout.addWidget(QLabel(self.tr("音频文件:")), 0, 0)
        self.affirmation_file = QLineEdit()
        self.affirmation_file.setToolTip(self.tr("选择一个音频文件作为肯定语。"))
        layout.addWidget(self.affirmation_file, 0, 1)
        
        btn_browse_aff = QPushButton(self.tr("浏览..."))
        btn_browse_aff.clicked.connect(lambda: self.browse_file(self.affirmation_file, 
                                                              self.tr("音频文件 (*.mp3 *.wav)")))
        btn_browse_aff.setToolTip(self.tr("选择音频文件"))
        layout.addWidget(btn_browse_aff, 0, 2)
        
        # 肯定语文本输入
        layout.addWidget(QLabel(self.tr("肯定语:")), 1, 0)
        self.affirmation_text = QLineEdit()
        self.affirmation_text.setToolTip(self.tr("输入肯定语。"))
        layout.addWidget(self.affirmation_text, 1, 1, 1, 2)
        
        # 文本文件选择
        layout.addWidget(QLabel(self.tr("文本文件:")), 2, 0)
        self.text_file = QLineEdit()
        self.text_file.setToolTip(self.tr("选择一个文本文件作为肯定语。"))
        layout.addWidget(self.text_file, 2, 1)
        
        btn_browse_text = QPushButton(self.tr("浏览..."))
        btn_browse_text.clicked.connect(lambda: self.browse_file(self.text_file, 
                                                               self.tr("文本文件 (*.txt)")))
        btn_browse_text.setToolTip(self.tr("选择文本文件"))
        layout.addWidget(btn_browse_text, 2, 2)
        
        # TTS引擎选择
        layout.addWidget(QLabel(self.tr("TTS引擎:")), 3, 0)
        self.tts_engine = QComboBox()
        self.tts_engine.setToolTip(self.tr("选择从文本生成肯定语音频时要使用的TTS引擎。"))
        layout.addWidget(self.tts_engine, 3, 1)
        
        # 生成按钮
        self.generate_tts_btn = QPushButton(self.tr("生成"))
        self.generate_tts_btn.setToolTip(self.tr("通过TTS从文本生成肯定语。"))
        layout.addWidget(self.generate_tts_btn, 3, 2)
        
        # 录制设备选择
        layout.addWidget(QLabel(self.tr("录制设备:")), 4, 0)
        self.record_device = QComboBox()
        self.record_device.setToolTip(self.tr("选择录制肯定语音频时要使用的设备。"))
        layout.addWidget(self.record_device, 4, 1)
        
        # 开始/停止录制按钮
        self.record_btn = QPushButton(self.tr("开始录制"))
        self.record_btn.setCheckable(True)
        self.record_btn.setToolTip(self.tr("开始/停止录制肯定语。"))
        layout.addWidget(self.record_btn, 4, 2)
        
        # 音量滑条
        layout.addWidget(QLabel(self.tr("音量:")), 5, 0)
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
        layout.addWidget(QLabel(self.tr("频率模式:")), 6, 0)
        self.frequency_mode = QComboBox()
        self.frequency_mode.addItems([self.tr("Raw（保持不变）"), 
                                     self.tr("UG（亚超声波）"), 
                                     self.tr("传统（次声波）")])
        self.frequency_mode.setToolTip(self.tr("改变肯定语音轨的频率，推荐使用地下（UG）模式。"))
        layout.addWidget(self.frequency_mode, 6, 1, 1, 2)
        
        # 倍速滑条
        layout.addWidget(QLabel(self.tr("倍速:")), 7, 0)
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
        overlay_group = QGroupBox(self.tr("叠加设置"))
        overlay_layout = QGridLayout()
        
        # 叠加次数
        overlay_layout.addWidget(QLabel(self.tr("叠加次数:")), 0, 0)
        self.overlay_times = QSpinBox()
        self.overlay_times.setRange(1, 10)
        self.overlay_times.setValue(1)
        self.overlay_times.setToolTip(self.tr("肯定语音轨的叠加次数。"))
        overlay_layout.addWidget(self.overlay_times, 0, 1)
        
        # 叠加间隔
        overlay_layout.addWidget(QLabel(self.tr("间隔:")), 1, 0)
        self.overlay_interval = QDoubleSpinBox()
        self.overlay_interval.setRange(0.0, 10.0)
        self.overlay_interval.setValue(1.0)
        self.overlay_interval.setSingleStep(0.1)
        self.overlay_interval.setToolTip(self.tr("每次叠加后，下一个叠加音轨应比上一个延后多少时间？"))
        overlay_layout.addWidget(self.overlay_interval, 1, 1)
        
        # 音量递减速率
        overlay_layout.addWidget(QLabel(self.tr("音量递减:")), 2, 0)
        self.volume_decrease = QDoubleSpinBox()
        self.volume_decrease.setRange(0.0, 10.0)
        self.volume_decrease.setValue(0.0)
        self.volume_decrease.setSingleStep(0.5)
        self.volume_decrease.setToolTip(self.tr("每次叠加后，下一个叠加音轨应比上一个音量降低多少？"))
        overlay_layout.addWidget(self.volume_decrease, 2, 1)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group, 9, 0, 1, 3)
        
        group_box.setLayout(layout)
        return group_box
    
    def create_background_group(self):
        """创建背景音组"""
        group_box = QGroupBox(self.tr("背景音"))
        layout = QGridLayout()
        
        # 文件选择
        layout.addWidget(QLabel(self.tr("背景音文件:")), 0, 0)
        self.background_file = QLineEdit()
        self.background_file.setToolTip(self.tr("选择一个音频文件作为背景音。"))
        layout.addWidget(self.background_file, 0, 1)
        
        btn_browse_bg = QPushButton(self.tr("浏览..."))
        btn_browse_bg.clicked.connect(lambda: self.browse_file(self.background_file, 
                                                              self.tr("音频文件 (*.mp3 *.wav)")))
        btn_browse_bg.setToolTip(self.tr("选择背景音频文件"))
        layout.addWidget(btn_browse_bg, 0, 2)
        
        # 音量滑条
        layout.addWidget(QLabel(self.tr("音量:")), 1, 0)
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
        
        group_box.setLayout(layout)
        return group_box
    
    def create_output_group(self):
        """创建输出组"""
        group_box = QGroupBox(self.tr("输出"))
        layout = QGridLayout()
        
        row = 0
        
        # 生成音频复选框
        self.generate_audio = QCheckBox(self.tr("生成音频"))
        self.generate_audio.setChecked(True)
        self.generate_audio.setToolTip(self.tr("是否生成音频。"))
        layout.addWidget(self.generate_audio, row, 0, 1, 2)
        
        # 音频设置组
        audio_group = QGroupBox(self.tr("音频设置"))
        audio_layout = QGridLayout()
        
        audio_layout.addWidget(QLabel(self.tr("格式:")), 0, 0)
        self.audio_format = QComboBox()
        self.audio_format.addItems(["WAV", "MP3"])
        audio_layout.addWidget(self.audio_format, 0, 1)
        
        audio_layout.addWidget(QLabel(self.tr("采样率:")), 1, 0)
        self.audio_sample_rate = QComboBox()
        self.audio_sample_rate.addItems(["44100 Hz", "48000 Hz", "96000 Hz", "192000 Hz"])
        audio_layout.addWidget(self.audio_sample_rate, 1, 1)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group, row+1, 0, 1, 3)
        
        row += 2
        
        # 生成视频复选框
        self.generate_video = QCheckBox(self.tr("生成视频"))
        self.generate_video.setToolTip(self.tr("是否生成视频。"))
        layout.addWidget(self.generate_video, row, 0, 1, 2)
        
        # 视频设置组
        video_group = QGroupBox(self.tr("视频设置"))
        video_layout = QGridLayout()
        
        # 视觉化图片选择
        video_layout.addWidget(QLabel(self.tr("视觉化图片:")), 0, 0)
        self.video_image = QLineEdit()
        self.video_image.setToolTip(self.tr("选择一个图片文件作为视觉化。"))
        video_layout.addWidget(self.video_image, 0, 1, 1, 2)
        
        btn_browse_image = QPushButton(self.tr("浏览..."))
        btn_browse_image.clicked.connect(lambda: self.browse_file(self.video_image, 
                                                                 self.tr("图片文件 (*.jpg *.jpeg *.png *.bmp)")))
        btn_browse_image.setToolTip(self.tr("选择视觉化图片"))
        video_layout.addWidget(btn_browse_image, 0, 3)
        
        # 搜索视觉化图片
        video_layout.addWidget(QLabel(self.tr("搜索关键词:")), 1, 0)
        self.search_keyword = QLineEdit()
        self.search_keyword.setToolTip(self.tr("输入关键词。"))
        video_layout.addWidget(self.search_keyword, 1, 1, 1, 2)
        
        # 搜索引擎选择
        video_layout.addWidget(QLabel(self.tr("搜索引擎:")), 2, 0)
        self.search_engine = QComboBox()
        self.search_engine.addItems(["Bing", "Google", "DuckDuckGo"])
        self.search_engine.setToolTip(self.tr("搜索视觉化图片时使用的搜索引擎。"))
        video_layout.addWidget(self.search_engine, 2, 1)
        
        # 联机搜索按钮
        self.search_btn = QPushButton(self.tr("联机搜索"))
        self.search_btn.setToolTip(self.tr("联机搜索视觉化图片。"))
        video_layout.addWidget(self.search_btn, 2, 2, 1, 2)
        
        # 视频格式设置
        video_layout.addWidget(QLabel(self.tr("视频格式:")), 3, 0)
        self.video_format = QComboBox()
        self.video_format.addItems(["MP4", "AVI", "MKV"])
        video_layout.addWidget(self.video_format, 3, 1)
        
        video_layout.addWidget(QLabel(self.tr("音频采样率:")), 4, 0)
        self.video_audio_sample_rate = QComboBox()
        self.video_audio_sample_rate.addItems(["44100 Hz", "48000 Hz", "96000 Hz"])
        video_layout.addWidget(self.video_audio_sample_rate, 4, 1)
        
        video_layout.addWidget(QLabel(self.tr("码率:")), 5, 0)
        self.video_bitrate = QComboBox()
        self.video_bitrate.addItems(["128 kbps", "192 kbps", "256 kbps", "320 kbps"])
        video_layout.addWidget(self.video_bitrate, 5, 1)
        
        video_layout.addWidget(QLabel(self.tr("分辨率:")), 6, 0)
        self.video_resolution = QComboBox()
        self.video_resolution.addItems(["1920x1080", "1280x720", "854x480", "640x360"])
        video_layout.addWidget(self.video_resolution, 6, 1)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group, row+1, 0, 1, 3)
        
        row += 2
        
        # 必须选择至少一个提示
        self.selection_hint = QLabel(self.tr("* 必须至少选择生成音频或生成视频一项"))
        self.selection_hint.setStyleSheet("color: red;")
        layout.addWidget(self.selection_hint, row, 0, 1, 3)
        
        row += 1
        
        # 元数据组
        metadata_group = QGroupBox(self.tr("元数据"))
        metadata_layout = QGridLayout()
        
        metadata_layout.addWidget(QLabel(self.tr("标题:")), 0, 0)
        self.metadata_title = QLineEdit()
        self.metadata_title.setToolTip(self.tr("设置项目输出元数据中的标题。"))
        metadata_layout.addWidget(self.metadata_title, 0, 1)
        
        metadata_layout.addWidget(QLabel(self.tr("作者:")), 1, 0)
        self.metadata_author = QLineEdit()
        self.metadata_author.setToolTip(self.tr("设置项目输出元数据中的作者。"))
        metadata_layout.addWidget(self.metadata_author, 1, 1)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group, row, 0, 1, 3)
        
        row += 1
        
        # 生成按钮
        self.generate_btn = QPushButton(self.tr("生成项目"))
        self.generate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-size: 14pt; padding: 10px; }")
        self.generate_btn.setToolTip(self.tr("开始生成项目！"))
        self.generate_btn.clicked.connect(self.generate_project)
        layout.addWidget(self.generate_btn, row, 0, 1, 3)
        
        group_box.setLayout(layout)
        return group_box

# ---以上为界面部分，使用QtDesigner时请将生成的代码粘贴覆盖到上方，本界面相关逻辑即将在下方实现。---

    def browse_file(self, line_edit, file_filter):
        """浏览文件对话框"""
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("选择文件"), "", file_filter)
        if file_path:
            line_edit.setText(file_path)
    
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