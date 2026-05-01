import os
from loguru import logger
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt

class OutputManager:
    """输出管理器 - 处理最终输出生成功能"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _get_timestamp(self):
        """获取时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_project(self):
        """生成项目"""
        logger.debug("开始生成项目")

        if not self.main_window.generate_audio.isChecked() and not self.main_window.generate_video.isChecked():
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("必须至少选择生成音频或生成视频一项！"))
            return

        affirmation_file = self.main_window.affirmation_file.text()
        if self.main_window.generate_audio.isChecked() and not affirmation_file:
            QMessageBox.warning(self.main_window, self.main_window.tr("警告"),
                               self.main_window.tr("生成音频需要选择肯定语音频文件！"))
            return

        logger.debug(f"肯定语文件路径: {affirmation_file}")
        if affirmation_file:
            logger.debug(f"肯定语文件绝对路径: {os.path.abspath(affirmation_file)}")
            logger.debug(f"肯定语文件是否存在: {os.path.exists(affirmation_file)}")

        if not self.main_window.check_project_selected():
            return

        project_dir = self.main_window.get_current_project_dir()
        self.main_window.save_project_config(project_dir)

        if self.main_window.ensure_integrity_check.isChecked():
            if not self.main_window.validate_affirmation_integrity():
                return

        timestamp = self._get_timestamp()
        generate_audio = self.main_window.generate_audio.isChecked()
        generate_video = self.main_window.generate_video.isChecked()

        logger.debug(f"生成选项 - 音频: {generate_audio}, 视频: {generate_video}")

        audio_format = self.main_window.audio_format.currentText()
        format_ext = audio_format.lower()

        if generate_video and not generate_audio:
            import tempfile
            temp_dir = tempfile.gettempdir()
            audio_output_path = os.path.join(temp_dir, f"SMake_temp_audio_{timestamp}.wav")
            logger.debug(f"使用临时音频路径: {audio_output_path}")
        else:
            audio_output_path = os.path.join(project_dir, "Releases", "Audio", f"{timestamp}.{format_ext}")
            logger.debug(f"使用项目音频路径: {audio_output_path}")

        output_dir = os.path.dirname(audio_output_path)
        if output_dir and not os.path.exists(output_dir):
            logger.debug(f"创建输出目录: {os.path.abspath(output_dir)}")
            os.makedirs(output_dir, exist_ok=True)

        params = {
            'affirmation_file': affirmation_file,
            'background_file': self.main_window.background_file.text(),
            'volume': self.main_window.affirmation_volume_spin.value(),
            'frequency_mode': self.main_window.frequency_mode.currentIndex(),
            'speed': self.main_window.speed_spin.value(),
            'reverse': self.main_window.reverse_check.isChecked(),
            'overlay_times': self.main_window.overlay_times.value(),
            'overlay_interval': self.main_window.overlay_interval.value(),
            'volume_decrease': self.main_window.volume_decrease.value(),
            'background_volume': self.main_window.background_volume_spin.value(),
            'freq_track_enabled': self.main_window.freq_track_enabled.isChecked(),
            'freq_track_freq': self.main_window.freq_track_freq.text(),
            'freq_track_volume': self.main_window.freq_track_volume.value(),
            'output_format': self.main_window.audio_format.currentText(),
            'output_path': audio_output_path,
            'generate_audio': generate_audio,
            'generate_video': generate_video,
            'video_image': self.main_window.video_image.text(),
            'video_format': self.main_window.video_format.currentText(),
            'video_resolution': self.main_window.video_resolution.currentText(),
            'metadata_title': self.main_window.metadata_title.text(),
            'metadata_author': self.main_window.metadata_author.text(),
            'ensure_integrity': self.main_window.ensure_integrity_check.isChecked()
        }

        logger.debug(f"生成项目参数 - output_path: {audio_output_path}")
        logger.debug(f"生成项目参数 - affirmation_file: {affirmation_file}")
        logger.debug(f"生成项目参数 - background_file: {self.main_window.background_file.text()}")
        logger.debug(f"生成项目参数 - video_image: {self.main_window.video_image.text()}")
        logger.debug(f"生成项目参数 - freq_track_enabled: {params['freq_track_enabled']}")
        logger.debug(f"生成项目参数 - freq_track_freq: {params['freq_track_freq']}")
        logger.debug(f"生成项目参数 - freq_track_volume: {params['freq_track_volume']}")

        self.main_window.progress_dialog = QProgressDialog(
            self.main_window.tr("正在生成项目..."),
            self.main_window.tr("取消"),
            0, 100,
            self.main_window
        )
        self.main_window.progress_dialog.setWindowModality(Qt.WindowModal)
        self.main_window.progress_dialog.setMinimumDuration(0)
        self.main_window.progress_dialog.setValue(0)
        self.main_window.progress_dialog.canceled.connect(self.main_window.cancel_generation)
        self.main_window.progress_dialog.show()

        self.main_window.current_generation_params = params

        from Processors.AudioProcessor import AudioProcessor
        self.main_window.audio_processor = AudioProcessor(params)
        self.main_window.audio_processor.progress_updated.connect(self.main_window.update_progress)
        self.main_window.audio_processor.processing_finished.connect(self.main_window.on_generation_finished)
        self.main_window.audio_processor.processing_error.connect(self.main_window.on_generation_error)
        self.main_window.audio_processor.start()

        logger.info("开始生成项目")

    def update_progress(self, value):
        """更新进度"""
        if hasattr(self.main_window, 'progress_dialog') and self.main_window.progress_dialog:
            self.main_window.progress_dialog.setValue(value)

    def cancel_generation(self):
        """取消生成"""
        if hasattr(self.main_window, 'audio_processor') and self.main_window.audio_processor and self.main_window.audio_processor.isRunning():
            self.main_window.audio_processor.cancel()
            self.main_window.audio_processor.wait()
            logger.info("用户取消音频生成")

        if hasattr(self.main_window, 'video_processor') and self.main_window.video_processor and self.main_window.video_processor.isRunning():
            self.main_window.video_processor.cancel()
            self.main_window.video_processor.wait()
            logger.info("用户取消视频生成")

    def on_generation_finished(self, output_path):
        """生成完成回调"""
        logger.info(f"音频生成完成: {output_path}")

        if hasattr(self.main_window, 'current_generation_params') and self.main_window.current_generation_params.get('generate_video'):
            self.start_video_generation(output_path)
        else:
            if hasattr(self.main_window, 'progress_dialog') and self.main_window.progress_dialog:
                try:
                    self.main_window.progress_dialog.canceled.disconnect(self.main_window.cancel_generation)
                except:
                    pass
                self.main_window.progress_dialog.close()
                self.main_window.progress_dialog = None

            QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                                   self.main_window.tr(f"音频生成成功！\n保存路径: {output_path}"))
            # 刷新输出文件列表
            if (hasattr(self.main_window, 'release_manager') and self.main_window.release_manager and
                self.main_window.release_manager.output_list is not None):
                self.main_window.release_manager.refresh_output_list()

    def start_video_generation(self, audio_path):
        """开始视频生成"""
        try:
            params = self.main_window.current_generation_params
            project_dir = self.main_window.get_current_project_dir()
            timestamp = self._get_timestamp()

            logger.debug(f"start_video_generation - audio_path: {audio_path}")
            logger.debug(f"start_video_generation - audio_path绝对路径: {os.path.abspath(audio_path)}")
            logger.debug(f"start_video_generation - audio_path是否存在: {os.path.exists(audio_path)}")

            video_format = params.get('video_format', 'MP4')
            format_ext = {
                'MP4': '.mp4',
                'AVI': '.avi',
                'MKV': '.mkv'
            }.get(video_format, '.mp4')

            video_output_path = os.path.join(project_dir, "Releases", "Video", f"{timestamp}{format_ext}")
            logger.debug(f"视频输出路径: {video_output_path}")
            logger.debug(f"视频输出绝对路径: {os.path.abspath(video_output_path)}")

            video_output_dir = os.path.dirname(video_output_path)
            if video_output_dir and not os.path.exists(video_output_dir):
                logger.debug(f"创建视频输出目录: {os.path.abspath(video_output_dir)}")
                os.makedirs(video_output_dir, exist_ok=True)

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

            if hasattr(self.main_window, 'progress_dialog') and self.main_window.progress_dialog:
                self.main_window.progress_dialog.setLabelText(self.main_window.tr("正在生成视频..."))
                self.main_window.progress_dialog.setValue(0)

            from Processors.VideoProcessor import VideoProcessor
            self.main_window.video_processor = VideoProcessor(video_params)
            self.main_window.video_processor.progress_updated.connect(self.main_window.update_progress)
            self.main_window.video_processor.processing_finished.connect(self.main_window.on_video_finished)
            self.main_window.video_processor.processing_error.connect(self.main_window.on_generation_error)
            self.main_window.video_processor.start()

        except Exception as e:
            logger.error(f"启动视频生成失败: {e}")
            QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                               self.main_window.tr(f"启动视频生成失败: {str(e)}"))

    def on_video_finished(self, output_path):
        """视频生成完成回调"""
        logger.info(f"视频生成完成: {output_path}")

        if hasattr(self.main_window, 'current_generation_params'):
            generate_audio = self.main_window.current_generation_params.get('generate_audio')
            if not generate_audio:
                try:
                    os.remove(self.main_window.current_generation_params.get('output_path'))
                    logger.debug("清理临时音频文件")
                except:
                    pass

        if hasattr(self.main_window, 'progress_dialog') and self.main_window.progress_dialog:
            try:
                self.main_window.progress_dialog.canceled.disconnect(self.main_window.cancel_generation)
            except:
                pass
            self.main_window.progress_dialog.close()
            self.main_window.progress_dialog = None

        QMessageBox.information(self.main_window, self.main_window.tr("成功"),
                               self.main_window.tr(f"视频生成成功！\n保存路径: {output_path}"))
        # 刷新输出文件列表
        if (hasattr(self.main_window, 'release_manager') and self.main_window.release_manager and
            self.main_window.release_manager.output_list is not None):
            self.main_window.release_manager.refresh_output_list()

    def on_generation_error(self, error_message):
        """生成错误回调"""
        logger.error(f"生成错误: {error_message}")

        if hasattr(self.main_window, 'progress_dialog') and self.main_window.progress_dialog:
            try:
                self.main_window.progress_dialog.canceled.disconnect(self.main_window.cancel_generation)
            except:
                pass
            self.main_window.progress_dialog.close()
            self.main_window.progress_dialog = None

        QMessageBox.critical(self.main_window, self.main_window.tr("错误"),
                           self.main_window.tr(f"生成失败: {error_message}"))