from PyQt5.QtWidgets import (
    QGroupBox, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QTextEdit, QSlider,
    QFrame, QScrollArea, QWidget, QListWidget
)
from PyQt5.QtCore import Qt, QSize
from loguru import logger

class UIFactory:
    """UI工厂类 - 负责创建所有UI组件"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def create_project_group(self):
        """创建项目管理组"""
        self.main_window.project_group = QGroupBox(self.main_window.tr("项目管理"))
        layout = QGridLayout()
        layout.setSpacing(10)

        # ===== 项目组区域 =====
        self.main_window.project_group_section = QGroupBox(self.main_window.tr("项目组"))
        group_section_layout = QGridLayout()
        group_section_layout.setSpacing(8)

        # 当前项目组显示
        self.main_window.label_current_project_group = QLabel(self.main_window.tr("当前:"))
        group_section_layout.addWidget(self.main_window.label_current_project_group, 0, 0)
        self.main_window.current_project_group_label = QLabel(self.main_window.tr("默认项目组"))
        self.main_window.current_project_group_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        group_section_layout.addWidget(self.main_window.current_project_group_label, 0, 1, 1, 2)

        # 项目组列表
        self.main_window.label_project_group_list = QLabel(self.main_window.tr("切换:"))
        group_section_layout.addWidget(self.main_window.label_project_group_list, 1, 0)
        self.main_window.project_group_list = QComboBox()
        self.main_window.project_group_list.setToolTip(self.main_window.tr("选择或切换当前项目组"))
        self.main_window.project_group_list.currentIndexChanged.connect(self.main_window.project_manager.on_project_group_selected)
        group_section_layout.addWidget(self.main_window.project_group_list, 1, 1, 1, 2)

        # 新建项目组
        self.main_window.label_new_project_group = QLabel(self.main_window.tr("新建:"))
        group_section_layout.addWidget(self.main_window.label_new_project_group, 2, 0)
        self.main_window.new_project_group_name = QLineEdit()
        self.main_window.new_project_group_name.setToolTip(self.main_window.tr("输入新项目组名称"))
        self.main_window.new_project_group_name.setPlaceholderText(self.main_window.tr("项目组名称"))
        group_section_layout.addWidget(self.main_window.new_project_group_name, 2, 1)

        self.main_window.create_project_group_btn = QPushButton(self.main_window.tr("创建"))
        self.main_window.create_project_group_btn.setToolTip(self.main_window.tr("创建新项目组"))
        self.main_window.create_project_group_btn.clicked.connect(self.main_window.project_manager.create_new_project_group)
        group_section_layout.addWidget(self.main_window.create_project_group_btn, 2, 2)

        # 删除项目组按钮
        self.main_window.delete_project_group_btn = QPushButton(self.main_window.tr("删除项目组"))
        self.main_window.delete_project_group_btn.setToolTip(self.main_window.tr("删除选中的项目组"))
        self.main_window.delete_project_group_btn.clicked.connect(self.main_window.project_manager.delete_project_group)
        group_section_layout.addWidget(self.main_window.delete_project_group_btn, 3, 0, 1, 3)

        self.main_window.project_group_section.setLayout(group_section_layout)
        layout.addWidget(self.main_window.project_group_section, 0, 0, 1, 3)

        # ===== 项目区域 =====
        self.main_window.project_section = QGroupBox(self.main_window.tr("项目"))
        project_section_layout = QGridLayout()
        project_section_layout.setSpacing(8)

        # 当前项目显示
        self.main_window.label_current_project = QLabel(self.main_window.tr("当前:"))
        project_section_layout.addWidget(self.main_window.label_current_project, 0, 0)
        self.main_window.current_project_label = QLabel(self.main_window.tr("未选择项目"))
        self.main_window.current_project_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        project_section_layout.addWidget(self.main_window.current_project_label, 0, 1, 1, 2)

        # 项目列表和操作按钮行
        project_list_row = QHBoxLayout()
        self.main_window.label_project_list = QLabel(self.main_window.tr("切换:"))
        project_list_row.addWidget(self.main_window.label_project_list)
        
        self.main_window.project_list = QComboBox()
        self.main_window.project_list.setToolTip(self.main_window.tr("选择或切换当前项目"))
        self.main_window.project_list.currentIndexChanged.connect(self.main_window.project_manager.on_project_selected)
        project_list_row.addWidget(self.main_window.project_list, 1)

        self.main_window.refresh_projects_btn = QPushButton(self.main_window.tr("刷新"))
        self.main_window.refresh_projects_btn.setToolTip(self.main_window.tr("刷新项目列表"))
        self.main_window.refresh_projects_btn.clicked.connect(self.main_window.project_manager.refresh_project_list)
        project_list_row.addWidget(self.main_window.refresh_projects_btn)
        
        project_section_layout.addLayout(project_list_row, 1, 0, 1, 3)

        # 新建项目
        self.main_window.label_new_project = QLabel(self.main_window.tr("新建:"))
        project_section_layout.addWidget(self.main_window.label_new_project, 2, 0)
        self.main_window.new_project_name = QLineEdit()
        self.main_window.new_project_name.setToolTip(self.main_window.tr("输入新项目名称"))
        self.main_window.new_project_name.setPlaceholderText(self.main_window.tr("项目名称"))
        project_section_layout.addWidget(self.main_window.new_project_name, 2, 1)

        self.main_window.create_project_btn = QPushButton(self.main_window.tr("创建"))
        self.main_window.create_project_btn.setToolTip(self.main_window.tr("创建新项目"))
        self.main_window.create_project_btn.clicked.connect(self.main_window.project_manager.create_project)
        project_section_layout.addWidget(self.main_window.create_project_btn, 2, 2)

        # 项目操作按钮行（复制、剪切、删除）
        project_ops_row = QHBoxLayout()
        project_ops_row.setSpacing(5)

        self.main_window.copy_project_btn = QPushButton(self.main_window.tr("复制"))
        self.main_window.copy_project_btn.setToolTip(self.main_window.tr("复制项目到当前项目组"))
        self.main_window.copy_project_btn.clicked.connect(self.main_window.project_manager.copy_project)
        project_ops_row.addWidget(self.main_window.copy_project_btn)

        self.main_window.cut_project_btn = QPushButton(self.main_window.tr("剪切"))
        self.main_window.cut_project_btn.setToolTip(self.main_window.tr("剪切项目到其他项目组"))
        self.main_window.cut_project_btn.clicked.connect(self.main_window.project_manager.cut_project)
        project_ops_row.addWidget(self.main_window.cut_project_btn)

        self.main_window.delete_project_btn = QPushButton(self.main_window.tr("删除"))
        self.main_window.delete_project_btn.setToolTip(self.main_window.tr("删除选中的项目"))
        self.main_window.delete_project_btn.clicked.connect(self.main_window.project_manager.delete_project)
        project_ops_row.addWidget(self.main_window.delete_project_btn)
        
        project_section_layout.addLayout(project_ops_row, 3, 0, 1, 3)

        # 项目路径信息
        self.main_window.label_project_path = QLabel(self.main_window.tr("路径:"))
        project_section_layout.addWidget(self.main_window.label_project_path, 4, 0)
        self.main_window.project_path_label = QLabel("./Project/")
        self.main_window.project_path_label.setStyleSheet("color: gray;")
        self.main_window.project_path_label.setWordWrap(True)
        project_section_layout.addWidget(self.main_window.project_path_label, 4, 1, 1, 2)

        self.main_window.project_section.setLayout(project_section_layout)
        layout.addWidget(self.main_window.project_section, 1, 0, 1, 3)

        # ===== 导入导出区域 =====
        self.main_window.import_export_section = QGroupBox(self.main_window.tr("导入/导出"))
        import_export_layout = QGridLayout()
        import_export_layout.setSpacing(8)

        self.main_window.export_project_btn = QPushButton(self.main_window.tr("导出项目"))
        self.main_window.export_project_btn.setToolTip(self.main_window.tr("将当前项目导出为压缩文件"))
        self.main_window.export_project_btn.clicked.connect(self.main_window.export_project)
        import_export_layout.addWidget(self.main_window.export_project_btn, 0, 0)

        self.main_window.export_project_group_btn = QPushButton(self.main_window.tr("导出项目组"))
        self.main_window.export_project_group_btn.setToolTip(self.main_window.tr("将当前项目组导出为压缩文件"))
        self.main_window.export_project_group_btn.clicked.connect(self.main_window.export_project_group)
        import_export_layout.addWidget(self.main_window.export_project_group_btn, 0, 1)

        self.main_window.import_btn = QPushButton(self.main_window.tr("导入"))
        self.main_window.import_btn.setToolTip(self.main_window.tr("从压缩文件导入项目或项目组"))
        self.main_window.import_btn.clicked.connect(self.main_window.import_project_or_group)
        import_export_layout.addWidget(self.main_window.import_btn, 0, 2)

        self.main_window.import_export_section.setLayout(import_export_layout)
        layout.addWidget(self.main_window.import_export_section, 2, 0, 1, 3)

        # ===== 项目结构说明 =====
        self.main_window.project_structure_group = QGroupBox(self.main_window.tr("项目结构"))
        structure_layout = QVBoxLayout()
        self.main_window.project_structure_label = QLabel(
            self.main_window.tr("项目组名称/\n"
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
        self.main_window.project_structure_label.setStyleSheet("font-family: monospace; color: #666;")
        structure_layout.addWidget(self.main_window.project_structure_label)
        self.main_window.project_structure_group.setLayout(structure_layout)
        layout.addWidget(self.main_window.project_structure_group, 3, 0, 1, 3)

        self.main_window.project_group.setLayout(layout)

        # 注意：项目组列表的刷新被延迟到所有UI组件创建完成后
        # 在Main_Window.initUI()的最后调用

        return self.main_window.project_group

    def create_affirmation_group(self):
        """创建肯定语组"""
        self.main_window.affirmation_group = QGroupBox(self.main_window.tr("肯定语"))
        layout = QGridLayout()

        # 文件选择
        self.main_window.label_audio_file = QLabel(self.main_window.tr("音频文件:"))
        layout.addWidget(self.main_window.label_audio_file, 0, 0)
        self.main_window.affirmation_file = QLineEdit()
        self.main_window.affirmation_file.setToolTip(self.main_window.tr("选择一个音频文件作为肯定语。"))
        layout.addWidget(self.main_window.affirmation_file, 0, 1)

        self.main_window.btn_browse_aff = QPushButton(self.main_window.tr("浏览..."))
        self.main_window.btn_browse_aff.clicked.connect(
            lambda: self.main_window.browse_file(self.main_window.affirmation_file,
                                              self.main_window.tr("音频文件 (*.mp3 *.wav)")))
        self.main_window.btn_browse_aff.setToolTip(self.main_window.tr("选择音频文件"))
        layout.addWidget(self.main_window.btn_browse_aff, 0, 2)

        # 肯定语文本输入
        self.main_window.label_affirmation_text = QLabel(self.main_window.tr("肯定语:"))
        layout.addWidget(self.main_window.label_affirmation_text, 1, 0)
        self.main_window.affirmation_text = QLineEdit()
        self.main_window.affirmation_text.setToolTip(self.main_window.tr("输入肯定语。"))
        layout.addWidget(self.main_window.affirmation_text, 1, 1, 1, 2)

        # 文本文件选择
        self.main_window.label_text_file = QLabel(self.main_window.tr("文本文件:"))
        layout.addWidget(self.main_window.label_text_file, 2, 0)
        self.main_window.text_file = QLineEdit()
        self.main_window.text_file.setToolTip(self.main_window.tr("选择一个文本文件作为肯定语。"))
        layout.addWidget(self.main_window.text_file, 2, 1)

        self.main_window.btn_browse_text = QPushButton(self.main_window.tr("浏览..."))
        self.main_window.btn_browse_text.clicked.connect(
            lambda: self.main_window.browse_file(self.main_window.text_file,
                                               self.main_window.tr("文本文件 (*.txt)")))
        self.main_window.btn_browse_text.setToolTip(self.main_window.tr("选择文本文件"))
        layout.addWidget(self.main_window.btn_browse_text, 2, 2)

        # TTS引擎选择
        self.main_window.label_tts_engine = QLabel(self.main_window.tr("TTS引擎:"))
        layout.addWidget(self.main_window.label_tts_engine, 3, 0)
        self.main_window.tts_engine = QComboBox()
        self.main_window.tts_engine.setToolTip(self.main_window.tr("选择从文本生成肯定语音频时要使用的TTS引擎。"))
        layout.addWidget(self.main_window.tts_engine, 3, 1)

        # 生成按钮
        self.main_window.generate_tts_btn = QPushButton(self.main_window.tr("生成"))
        self.main_window.generate_tts_btn.setToolTip(self.main_window.tr("通过TTS从文本生成肯定语。"))
        self.main_window.generate_tts_btn.clicked.connect(self.main_window.tts_manager.generate_tts_audio)
        layout.addWidget(self.main_window.generate_tts_btn, 3, 2)

        # 录制设备选择
        self.main_window.label_record_device = QLabel(self.main_window.tr("录制设备:"))
        layout.addWidget(self.main_window.label_record_device, 4, 0)
        self.main_window.record_device = QComboBox()
        self.main_window.record_device.setToolTip(self.main_window.tr("选择录制肯定语音频时要使用的设备。"))
        layout.addWidget(self.main_window.record_device, 4, 1)

        # 开始/停止录制按钮
        self.main_window.record_btn = QPushButton(self.main_window.tr("开始录制"))
        self.main_window.record_btn.setCheckable(True)
        self.main_window.record_btn.setToolTip(self.main_window.tr("开始/停止录制肯定语。"))
        self.main_window.record_btn.clicked.connect(self.main_window.recording_manager.toggle_recording)
        layout.addWidget(self.main_window.record_btn, 4, 2)

        # 音量滑条
        self.main_window.label_volume = QLabel(self.main_window.tr("音量:"))
        layout.addWidget(self.main_window.label_volume, 5, 0)
        self.main_window.affirmation_volume = QSlider(Qt.Horizontal)
        self.main_window.affirmation_volume.setRange(-600, 0)
        self.main_window.affirmation_volume.setValue(-230)
        self.main_window.affirmation_volume.setToolTip(self.main_window.tr("改变肯定语音轨的音量。（单位为分贝）"))
        layout.addWidget(self.main_window.affirmation_volume, 5, 1)

        self.main_window.affirmation_volume_spin = QDoubleSpinBox()
        self.main_window.affirmation_volume_spin.setRange(-60.0, 0.0)
        self.main_window.affirmation_volume_spin.setValue(-23.0)
        self.main_window.affirmation_volume_spin.setSingleStep(0.5)
        self.main_window.affirmation_volume_spin.valueChanged.connect(
            lambda v: self.main_window.affirmation_volume.setValue(int(v * 10)))
        self.main_window.affirmation_volume.valueChanged.connect(
            lambda v: self.main_window.affirmation_volume_spin.setValue(v / 10.0))
        layout.addWidget(self.main_window.affirmation_volume_spin, 5, 2)

        # 频率选择
        self.main_window.label_freq_mode = QLabel(self.main_window.tr("频率模式:"))
        layout.addWidget(self.main_window.label_freq_mode, 6, 0)
        self.main_window.frequency_mode = QComboBox()
        self.main_window.frequency_mode.addItems([self.main_window.tr("Raw（保持不变）"),
                                                 self.main_window.tr("UG（亚超声波）"),
                                                 self.main_window.tr("传统（次声波）")])
        self.main_window.frequency_mode.setToolTip(self.main_window.tr("改变肯定语音轨的频率，推荐使用地下（UG）模式。"))
        layout.addWidget(self.main_window.frequency_mode, 6, 1, 1, 2)

        # 倍速滑条
        self.main_window.label_speed = QLabel(self.main_window.tr("倍速:"))
        layout.addWidget(self.main_window.label_speed, 7, 0)
        self.main_window.speed_slider = QSlider(Qt.Horizontal)
        self.main_window.speed_slider.setRange(10, 100)
        self.main_window.speed_slider.setValue(10)
        self.main_window.speed_slider.setToolTip(self.main_window.tr("改变肯定语音轨的倍速。"))
        layout.addWidget(self.main_window.speed_slider, 7, 1)

        self.main_window.speed_spin = QDoubleSpinBox()
        self.main_window.speed_spin.setRange(1.0, 10.0)
        self.main_window.speed_spin.setValue(1.0)
        self.main_window.speed_spin.setSingleStep(0.1)
        self.main_window.speed_spin.valueChanged.connect(
            lambda v: self.main_window.speed_slider.setValue(int(v * 10)))
        self.main_window.speed_slider.valueChanged.connect(
            lambda v: self.main_window.speed_spin.setValue(v / 10.0))
        layout.addWidget(self.main_window.speed_spin, 7, 2)

        # 倒放复选框
        self.main_window.reverse_check = QCheckBox(self.main_window.tr("倒放"))
        self.main_window.reverse_check.setToolTip(self.main_window.tr("肯定语是否倒放。"))
        layout.addWidget(self.main_window.reverse_check, 8, 1, 1, 2)

        # 叠加组
        self.main_window.overlay_group = QGroupBox(self.main_window.tr("叠加设置"))
        overlay_layout = QGridLayout()

        # 叠加次数
        self.main_window.label_overlay_times = QLabel(self.main_window.tr("叠加次数:"))
        overlay_layout.addWidget(self.main_window.label_overlay_times, 0, 0)
        self.main_window.overlay_times = QSpinBox()
        self.main_window.overlay_times.setRange(1, 10)
        self.main_window.overlay_times.setValue(1)
        self.main_window.overlay_times.setToolTip(self.main_window.tr("肯定语音轨的叠加次数。"))
        overlay_layout.addWidget(self.main_window.overlay_times, 0, 1)

        # 叠加间隔
        self.main_window.label_overlay_interval = QLabel(self.main_window.tr("间隔:"))
        overlay_layout.addWidget(self.main_window.label_overlay_interval, 1, 0)
        self.main_window.overlay_interval = QDoubleSpinBox()
        self.main_window.overlay_interval.setRange(0.0, 10.0)
        self.main_window.overlay_interval.setValue(1.0)
        self.main_window.overlay_interval.setSingleStep(0.1)
        self.main_window.overlay_interval.setToolTip(self.main_window.tr("每次叠加后，下一个叠加音轨应比上一个延后多少时间？"))
        overlay_layout.addWidget(self.main_window.overlay_interval, 1, 1)

        # 音量递减速率
        self.main_window.label_volume_decrease = QLabel(self.main_window.tr("音量递减:"))
        overlay_layout.addWidget(self.main_window.label_volume_decrease, 2, 0)
        self.main_window.volume_decrease = QDoubleSpinBox()
        self.main_window.volume_decrease.setRange(0.0, 10.0)
        self.main_window.volume_decrease.setValue(0.0)
        self.main_window.volume_decrease.setSingleStep(0.5)
        self.main_window.volume_decrease.setToolTip(self.main_window.tr("每次叠加后，下一个叠加音轨应比上一个音量降低多少？"))
        overlay_layout.addWidget(self.main_window.volume_decrease, 2, 1)

        self.main_window.overlay_group.setLayout(overlay_layout)
        layout.addWidget(self.main_window.overlay_group, 9, 0, 1, 3)

        # 确保肯定语完整性复选框
        self.main_window.ensure_integrity_check = QCheckBox(self.main_window.tr("确保肯定语完整性"))
        self.main_window.ensure_integrity_check.setToolTip(self.main_window.tr("启用后，肯定语将在背景音乐中完整循环播放，不会被截断。如果肯定语比背景音乐长，将阻止生成。"))
        layout.addWidget(self.main_window.ensure_integrity_check, 10, 0, 1, 3)

        self.main_window.affirmation_group.setLayout(layout)
        return self.main_window.affirmation_group

    def create_background_group(self):
        """创建背景音组"""
        self.main_window.background_group = QGroupBox(self.main_window.tr("背景音"))
        layout = QGridLayout()

        # 文件选择
        self.main_window.label_bg_file = QLabel(self.main_window.tr("背景音文件:"))
        layout.addWidget(self.main_window.label_bg_file, 0, 0)
        self.main_window.background_file = QLineEdit()
        self.main_window.background_file.setToolTip(self.main_window.tr("选择一个音频文件作为背景音。"))
        layout.addWidget(self.main_window.background_file, 0, 1)

        self.main_window.btn_browse_bg = QPushButton(self.main_window.tr("浏览..."))
        self.main_window.btn_browse_bg.clicked.connect(
            lambda: self.main_window.browse_file(self.main_window.background_file,
                                              self.main_window.tr("音频文件 (*.mp3 *.wav)")))
        self.main_window.btn_browse_bg.setToolTip(self.main_window.tr("选择背景音频文件"))
        layout.addWidget(self.main_window.btn_browse_bg, 0, 2)

        # 音量滑条
        self.main_window.label_bg_volume = QLabel(self.main_window.tr("音量:"))
        layout.addWidget(self.main_window.label_bg_volume, 1, 0)
        self.main_window.background_volume = QSlider(Qt.Horizontal)
        self.main_window.background_volume.setRange(-600, 0)
        self.main_window.background_volume.setValue(0)
        self.main_window.background_volume.setToolTip(self.main_window.tr("改变背景音音轨的音量。（单位为分贝）"))
        layout.addWidget(self.main_window.background_volume, 1, 1)

        self.main_window.background_volume_spin = QDoubleSpinBox()
        self.main_window.background_volume_spin.setRange(-60.0, 0.0)
        self.main_window.background_volume_spin.setValue(0.0)
        self.main_window.background_volume_spin.setSingleStep(0.5)
        self.main_window.background_volume_spin.valueChanged.connect(
            lambda v: self.main_window.background_volume.setValue(int(v * 10)))
        self.main_window.background_volume.valueChanged.connect(
            lambda v: self.main_window.background_volume_spin.setValue(v / 10.0))
        layout.addWidget(self.main_window.background_volume_spin, 1, 2)

        self.main_window.background_group.setLayout(layout)
        return self.main_window.background_group

    def create_freq_track_group(self):
        """创建特定频率音轨组"""
        self.main_window.freq_track_group = QGroupBox(self.main_window.tr("特定频率音轨"))
        layout = QGridLayout()

        # 启用特定频率音轨
        self.main_window.freq_track_enabled = QCheckBox(self.main_window.tr("启用特定频率音轨"))
        self.main_window.freq_track_enabled.setChecked(False)
        self.main_window.freq_track_enabled.setToolTip(self.main_window.tr("在音频中叠加特定频率的音轨。"))
        layout.addWidget(self.main_window.freq_track_enabled, 0, 0, 1, 3)

        # 频率选择
        self.main_window.label_freq_track_freq = QLabel(self.main_window.tr("频率 (Hz):"))
        layout.addWidget(self.main_window.label_freq_track_freq, 1, 0)
        self.main_window.freq_track_freq = QLineEdit()
        self.main_window.freq_track_freq.setText("432")
        self.main_window.freq_track_freq.setToolTip(self.main_window.tr("输入要叠加的特定频率(Hz)。"))
        layout.addWidget(self.main_window.freq_track_freq, 1, 1, 1, 2)

        # 音量设置
        self.main_window.label_freq_track_volume = QLabel(self.main_window.tr("音量 (dB):"))
        layout.addWidget(self.main_window.label_freq_track_volume, 2, 0)
        self.main_window.freq_track_volume = QDoubleSpinBox()
        self.main_window.freq_track_volume.setRange(-60.0, 0.0)
        self.main_window.freq_track_volume.setValue(-23.0)
        self.main_window.freq_track_volume.setSingleStep(1.0)
        self.main_window.freq_track_volume.setToolTip(self.main_window.tr("特定频率音轨的音量（分贝）。"))
        layout.addWidget(self.main_window.freq_track_volume, 2, 1, 1, 2)

        self.main_window.freq_track_group.setLayout(layout)
        return self.main_window.freq_track_group

    def create_output_group(self):
        """创建输出组"""
        self.main_window.output_group = QGroupBox(self.main_window.tr("输出"))
        layout = QGridLayout()

        row = 0

        # 生成音频复选框
        self.main_window.generate_audio = QCheckBox(self.main_window.tr("生成音频"))
        self.main_window.generate_audio.setChecked(True)
        self.main_window.generate_audio.setToolTip(self.main_window.tr("是否生成音频。"))
        self.main_window.generate_audio.toggled.connect(self.main_window.on_generate_audio_toggled)
        layout.addWidget(self.main_window.generate_audio, row, 0, 1, 2)

        # 音频设置组
        self.main_window.audio_group = QGroupBox(self.main_window.tr("音频设置"))
        audio_layout = QGridLayout()

        self.main_window.label_audio_format = QLabel(self.main_window.tr("格式:"))
        audio_layout.addWidget(self.main_window.label_audio_format, 0, 0)
        self.main_window.audio_format = QComboBox()
        self.main_window.audio_format.addItems(["WAV", "MP3"])
        audio_layout.addWidget(self.main_window.audio_format, 0, 1)

        self.main_window.label_audio_sample_rate = QLabel(self.main_window.tr("采样率:"))
        audio_layout.addWidget(self.main_window.label_audio_sample_rate, 1, 0)
        self.main_window.audio_sample_rate = QComboBox()
        self.main_window.audio_sample_rate.addItems(["44100 Hz", "48000 Hz", "96000 Hz", "192000 Hz"])
        audio_layout.addWidget(self.main_window.audio_sample_rate, 1, 1)

        self.main_window.audio_group.setLayout(audio_layout)
        layout.addWidget(self.main_window.audio_group, row+1, 0, 1, 3)

        row += 2

        # ffmpeg未安装提示
        self.main_window.ffmpeg_warning_label = QLabel()
        self.main_window.ffmpeg_warning_label.setText(
            self.main_window.tr('⚠️ 未检测到ffmpeg，视频生成和非WAV音频格式功能已被禁用。<a href="https://ffmpeg.org/download.html">点击下载ffmpeg</a>'))
        self.main_window.ffmpeg_warning_label.setStyleSheet("color: orange; font-weight: bold;")
        self.main_window.ffmpeg_warning_label.setVisible(False)
        self.main_window.ffmpeg_warning_label.setOpenExternalLinks(True)
        layout.addWidget(self.main_window.ffmpeg_warning_label, row, 0, 1, 3)

        row += 1

        # 生成视频复选框
        self.main_window.generate_video = QCheckBox(self.main_window.tr("生成视频"))
        self.main_window.generate_video.setToolTip(self.main_window.tr("是否生成视频。"))
        self.main_window.generate_video.toggled.connect(self.main_window.on_generate_video_toggled)
        layout.addWidget(self.main_window.generate_video, row, 0, 1, 2)

        # 视频设置组
        self.main_window.video_group = QGroupBox(self.main_window.tr("视频设置"))
        video_layout = QGridLayout()

        # 视觉化图片选择
        self.main_window.label_video_image = QLabel(self.main_window.tr("视觉化图片:"))
        video_layout.addWidget(self.main_window.label_video_image, 0, 0)
        self.main_window.video_image = QLineEdit()
        self.main_window.video_image.setToolTip(self.main_window.tr("选择一个图片文件作为视觉化。"))
        video_layout.addWidget(self.main_window.video_image, 0, 1, 1, 2)

        self.main_window.btn_browse_image = QPushButton(self.main_window.tr("浏览..."))
        self.main_window.btn_browse_image.clicked.connect(
            lambda: self.main_window.browse_file(self.main_window.video_image,
                                              self.main_window.tr("图片文件 (*.jpg *.jpeg *.png *.bmp)")))
        self.main_window.btn_browse_image.setToolTip(self.main_window.tr("选择视觉化图片"))
        video_layout.addWidget(self.main_window.btn_browse_image, 0, 3)

        # 搜索视觉化图片
        self.main_window.label_search_keyword = QLabel(self.main_window.tr("搜索关键词:"))
        video_layout.addWidget(self.main_window.label_search_keyword, 1, 0)
        self.main_window.search_keyword = QLineEdit()
        self.main_window.search_keyword.setToolTip(self.main_window.tr("输入关键词。"))
        video_layout.addWidget(self.main_window.search_keyword, 1, 1, 1, 2)

        # 搜索引擎选择
        self.main_window.label_search_engine = QLabel(self.main_window.tr("搜索引擎:"))
        video_layout.addWidget(self.main_window.label_search_engine, 2, 0)
        self.main_window.search_engine = QComboBox()
        self.main_window.search_engine.addItems(["Bing", "Google", "DuckDuckGo"])
        self.main_window.search_engine.setToolTip(self.main_window.tr("搜索视觉化图片时使用的搜索引擎。"))
        video_layout.addWidget(self.main_window.search_engine, 2, 1)

        # 联机搜索按钮
        self.main_window.search_btn = QPushButton(self.main_window.tr("联机搜索"))
        self.main_window.search_btn.setToolTip(self.main_window.tr("联机搜索视觉化图片。"))
        self.main_window.search_btn.clicked.connect(self.main_window.search_visualization_image)
        video_layout.addWidget(self.main_window.search_btn, 2, 2, 1, 2)

        # 视频格式设置
        self.main_window.label_video_format = QLabel(self.main_window.tr("视频格式:"))
        video_layout.addWidget(self.main_window.label_video_format, 3, 0)
        self.main_window.video_format = QComboBox()
        self.main_window.video_format.addItems(["MP4", "AVI", "MKV"])
        video_layout.addWidget(self.main_window.video_format, 3, 1)

        self.main_window.label_video_audio_sample_rate = QLabel(self.main_window.tr("音频采样率:"))
        video_layout.addWidget(self.main_window.label_video_audio_sample_rate, 4, 0)
        self.main_window.video_audio_sample_rate = QComboBox()
        self.main_window.video_audio_sample_rate.addItems(["44100 Hz", "48000 Hz", "96000 Hz"])
        video_layout.addWidget(self.main_window.video_audio_sample_rate, 4, 1)

        self.main_window.label_video_bitrate = QLabel(self.main_window.tr("码率:"))
        video_layout.addWidget(self.main_window.label_video_bitrate, 5, 0)
        self.main_window.video_bitrate = QComboBox()
        self.main_window.video_bitrate.addItems(["128 kbps", "192 kbps", "256 kbps", "320 kbps"])
        video_layout.addWidget(self.main_window.video_bitrate, 5, 1)

        self.main_window.label_video_resolution = QLabel(self.main_window.tr("分辨率:"))
        video_layout.addWidget(self.main_window.label_video_resolution, 6, 0)
        self.main_window.video_resolution = QComboBox()
        self.main_window.video_resolution.addItems(["1920x1080", "1280x720", "854x480", "640x360"])
        video_layout.addWidget(self.main_window.video_resolution, 6, 1)

        self.main_window.video_group.setLayout(video_layout)
        layout.addWidget(self.main_window.video_group, row+1, 0, 1, 3)

        row += 2

        # 必须选择至少一个提示
        self.main_window.selection_hint = QLabel(self.main_window.tr("* 必须至少选择生成音频或生成视频一项"))
        self.main_window.selection_hint.setStyleSheet("color: red;")
        layout.addWidget(self.main_window.selection_hint, row, 0, 1, 3)

        row += 1

        # 元数据组
        self.main_window.metadata_group = QGroupBox(self.main_window.tr("元数据"))
        metadata_layout = QGridLayout()

        self.main_window.label_metadata_title = QLabel(self.main_window.tr("标题:"))
        metadata_layout.addWidget(self.main_window.label_metadata_title, 0, 0)
        self.main_window.metadata_title = QLineEdit()
        self.main_window.metadata_title.setToolTip(self.main_window.tr("设置项目输出元数据中的标题。"))
        metadata_layout.addWidget(self.main_window.metadata_title, 0, 1)

        self.main_window.label_metadata_author = QLabel(self.main_window.tr("作者:"))
        metadata_layout.addWidget(self.main_window.label_metadata_author, 1, 0)
        self.main_window.metadata_author = QLineEdit()
        self.main_window.metadata_author.setToolTip(self.main_window.tr("设置项目输出元数据中的作者。"))
        metadata_layout.addWidget(self.main_window.metadata_author, 1, 1)

        self.main_window.metadata_group.setLayout(metadata_layout)
        layout.addWidget(self.main_window.metadata_group, row, 0, 1, 3)

        row += 1

        # 预览组
        self.main_window.preview_group = QGroupBox(self.main_window.tr("预览"))
        preview_layout = QVBoxLayout()

        # 预览控制按钮
        preview_control_layout = QHBoxLayout()

        self.main_window.preview_zoom_in_btn = QPushButton(self.main_window.tr("放大"))
        self.main_window.preview_zoom_in_btn.setToolTip(self.main_window.tr("放大预览视图"))
        self.main_window.preview_zoom_in_btn.clicked.connect(self.main_window.preview_manager.preview_zoom_in)
        preview_control_layout.addWidget(self.main_window.preview_zoom_in_btn)

        self.main_window.preview_zoom_out_btn = QPushButton(self.main_window.tr("缩小"))
        self.main_window.preview_zoom_out_btn.setToolTip(self.main_window.tr("缩小预览视图"))
        self.main_window.preview_zoom_out_btn.clicked.connect(self.main_window.preview_manager.preview_zoom_out)
        preview_control_layout.addWidget(self.main_window.preview_zoom_out_btn)

        self.main_window.preview_reset_btn = QPushButton(self.main_window.tr("重置视图"))
        self.main_window.preview_reset_btn.setToolTip(self.main_window.tr("重置预览视图缩放和位置"))
        self.main_window.preview_reset_btn.clicked.connect(self.main_window.preview_manager.preview_reset)
        preview_control_layout.addWidget(self.main_window.preview_reset_btn)

        self.main_window.preview_update_btn = QPushButton(self.main_window.tr("更新预览"))
        self.main_window.preview_update_btn.setToolTip(self.main_window.tr("根据当前配置更新预览"))
        self.main_window.preview_update_btn.clicked.connect(self.main_window.preview_manager.update_preview)
        preview_control_layout.addWidget(self.main_window.preview_update_btn)

        preview_control_layout.addStretch()
        preview_layout.addLayout(preview_control_layout)

        # 预览画布
        self.main_window.preview_scroll = QScrollArea()
        self.main_window.preview_scroll.setWidgetResizable(False)
        self.main_window.preview_scroll.setMinimumHeight(200)
        self.main_window.preview_scroll.setStyleSheet("QScrollArea { border: 1px solid #ccc; background-color: #f5f5f5; }")

        self.main_window.preview_widget = QWidget()
        self.main_window.preview_widget.setMinimumSize(800, 300)
        self.main_window.preview_layout = QVBoxLayout(self.main_window.preview_widget)
        self.main_window.preview_layout.setSpacing(10)
        self.main_window.preview_layout.setContentsMargins(10, 10, 10, 10)

        # 轨道标签
        self.main_window.preview_tracks_label = QLabel(self.main_window.tr('轨道预览（点击"更新预览"查看）'))
        self.main_window.preview_tracks_label.setAlignment(Qt.AlignCenter)
        self.main_window.preview_tracks_label.setStyleSheet("color: #666; font-size: 12px;")
        self.main_window.preview_layout.addWidget(self.main_window.preview_tracks_label)

        self.main_window.preview_scroll.setWidget(self.main_window.preview_widget)
        preview_layout.addWidget(self.main_window.preview_scroll)

        # 缩放比例显示
        self.main_window.preview_zoom_label = QLabel(self.main_window.tr("缩放: 100%"))
        self.main_window.preview_zoom_label.setAlignment(Qt.AlignRight)
        preview_layout.addWidget(self.main_window.preview_zoom_label)

        self.main_window.preview_group.setLayout(preview_layout)
        layout.addWidget(self.main_window.preview_group, row, 0, 1, 3)

        row += 1

        # 生成按钮
        self.main_window.generate_btn = QPushButton(self.main_window.tr("生成项目"))
        self.main_window.generate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-size: 14pt; padding: 10px; }")
        self.main_window.generate_btn.setToolTip(self.main_window.tr("开始生成项目！"))
        self.main_window.generate_btn.clicked.connect(self.main_window.output_manager.generate_project)
        layout.addWidget(self.main_window.generate_btn, row, 0, 1, 3)

        self.main_window.output_group.setLayout(layout)
        return self.main_window.output_group

    def create_settings_group(self):
        """创建设置组"""
        self.main_window.settings_group = QGroupBox(self.main_window.tr("设置"))
        layout = QGridLayout()

        # 语言设置
        self.main_window.label_language = QLabel(self.main_window.tr("语言:"))
        layout.addWidget(self.main_window.label_language, 0, 0)
        self.main_window.language_combo = QComboBox()

        # 动态加载所有可用的翻译文件
        available_translations = self.main_window.get_available_translations()
        for lang_code in sorted(available_translations.keys()):
            self.main_window.language_combo.addItem(lang_code, lang_code)

        # 设置当前选中的语言
        current_index = self.main_window.language_combo.findData(self.main_window.current_language)
        if current_index >= 0:
            self.main_window.language_combo.setCurrentIndex(current_index)

        self.main_window.language_combo.currentIndexChanged.connect(self.main_window.change_language)
        layout.addWidget(self.main_window.language_combo, 0, 1)

        # 应用语言按钮
        self.main_window.apply_language_btn = QPushButton(self.main_window.tr("应用语言"))
        self.main_window.apply_language_btn.clicked.connect(self.main_window.apply_language_settings)
        layout.addWidget(self.main_window.apply_language_btn, 0, 2)

        # 重置设置按钮
        self.main_window.reset_settings_btn = QPushButton(self.main_window.tr("重置设置"))
        self.main_window.reset_settings_btn.clicked.connect(self.main_window.reset_settings)
        layout.addWidget(self.main_window.reset_settings_btn, 1, 0, 1, 3)

        # 关于信息
        self.main_window.about_group = QGroupBox(self.main_window.tr("关于"))
        about_layout = QVBoxLayout()

        self.main_window.about_label = QLabel(self.main_window.tr("SMake"))
        self.main_window.about_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(self.main_window.about_label)

        self.main_window.about_group.setLayout(about_layout)
        layout.addWidget(self.main_window.about_group, 2, 0, 1, 3)

        self.main_window.settings_group.setLayout(layout)
        return self.main_window.settings_group

    def create_log_group(self):
        """创建日志输出组"""
        self.main_window.log_group = QGroupBox(self.main_window.tr("日志输出"))
        layout = QVBoxLayout()

        # 日志显示区域
        self.main_window.log_text_edit = QTextEdit()
        self.main_window.log_text_edit.setReadOnly(True)
        self.main_window.log_text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.main_window.log_text_edit.setStyleSheet("""
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
        layout.addWidget(self.main_window.log_text_edit)

        # 清空日志按钮
        button_layout = QGridLayout()
        self.main_window.clear_log_btn = QPushButton(self.main_window.tr("清空日志"))
        self.main_window.clear_log_btn.setToolTip(self.main_window.tr("清空日志显示区域"))
        self.main_window.clear_log_btn.clicked.connect(self.main_window.clear_log_display)
        button_layout.addWidget(self.main_window.clear_log_btn, 0, 0)

        # 添加弹性空间
        button_layout.setColumnStretch(1, 1)
        layout.addLayout(button_layout)

        self.main_window.log_group.setLayout(layout)
        return self.main_window.log_group

    def create_release_group(self):
        """创建输出文件管理组"""
        self.main_window.release_group = QGroupBox(self.main_window.tr("输出文件管理"))
        layout = QVBoxLayout()

        # 说明标签
        info_label = QLabel(self.main_window.tr("管理项目的输出文件（音频/视频）。双击文件可用系统播放器打开。"))
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 文件列表
        self.main_window.output_list = QListWidget()
        self.main_window.output_list.setIconSize(QSize(24, 24))
        self.main_window.output_list.setMinimumHeight(300)
        self.main_window.output_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: #f9f9f9;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        layout.addWidget(self.main_window.output_list)

        # 立即设置 release_manager 的 output_list
        if hasattr(self.main_window, 'release_manager') and self.main_window.release_manager:
            self.main_window.release_manager.setup_ui(self.main_window.output_list)

        self.main_window.release_group.setLayout(layout)
        return self.main_window.release_group