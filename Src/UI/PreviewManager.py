import os
from loguru import logger

class PreviewManager:
    """预览管理器 - 处理音频预览和时间轴显示"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.preview_zoom_level = 1.0
        
    def preview_zoom_in(self):
        """放大预览视图"""
        self.preview_zoom_level = min(self.preview_zoom_level * 1.2, 3.0)
        self._apply_preview_zoom()
        logger.debug(f"预览放大到: {self.preview_zoom_level:.0%}")

    def preview_zoom_out(self):
        """缩小预览视图"""
        self.preview_zoom_level = max(self.preview_zoom_level / 1.2, 0.3)
        self._apply_preview_zoom()
        logger.debug(f"预览缩小到: {self.preview_zoom_level:.0%}")

    def preview_reset(self):
        """重置预览视图"""
        self.preview_zoom_level = 1.0
        self._apply_preview_zoom()

        if hasattr(self.main_window, 'preview_scroll'):
            self.main_window.preview_scroll.horizontalScrollBar().setValue(0)
            self.main_window.preview_scroll.verticalScrollBar().setValue(0)

        logger.debug("预览视图已重置")

    def _apply_preview_zoom(self):
        """应用预览缩放"""
        if hasattr(self.main_window, 'preview_widget'):
            if hasattr(self.main_window, 'preview_zoom_label'):
                self.main_window.preview_zoom_label.setText(self.main_window.tr(f"缩放: {self.preview_zoom_level:.0%}"))

            self.update_preview()

            base_width = 800
            base_height = 300
            new_width = max(int(base_width * self.preview_zoom_level), 400)
            new_height = max(int(base_height * self.preview_zoom_level), 200)
            
            self.main_window.preview_widget.adjustSize()

    def update_preview(self):
        """更新预览视图"""
        logger.debug("开始更新预览")

        if hasattr(self.main_window, 'preview_layout'):
            while self.main_window.preview_layout.count() > 1:
                item = self.main_window.preview_layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()

        affirmation_file = self.main_window.affirmation_file.text() if hasattr(self.main_window, 'affirmation_file') else ""
        background_file = self.main_window.background_file.text() if hasattr(self.main_window, 'background_file') else ""

        if not affirmation_file and not background_file:
            if hasattr(self.main_window, 'preview_tracks_label'):
                self.main_window.preview_tracks_label.setText(self.main_window.tr("请先选择音频文件"))
            return

        try:
            tracks = []
            max_duration = 0

            if background_file and os.path.exists(background_file):
                duration = self._get_audio_duration(background_file)
                max_duration = max(max_duration, duration)
                tracks.append({
                    'name': self.main_window.tr("背景音乐"),
                    'file': background_file,
                    'color': "#4CAF50",
                    'volume': self.main_window.background_volume.value() if hasattr(self.main_window, 'background_volume') else 0,
                    'duration': duration,
                    'overlay_index': 0
                })

            if affirmation_file and os.path.exists(affirmation_file):
                duration = self._get_audio_duration(affirmation_file)
                tracks.append({
                    'name': self.main_window.tr("肯定语"),
                    'file': affirmation_file,
                    'color': "#2196F3",
                    'volume': self.main_window.affirmation_volume.value() if hasattr(self.main_window, 'affirmation_volume') else 0,
                    'duration': duration,
                    'overlay_index': 0
                })

            if hasattr(self.main_window, 'freq_track_enabled') and self.main_window.freq_track_enabled.isChecked():
                freq_track_duration = max_duration if max_duration > 0 else 60
                tracks.append({
                    'name': self.main_window.tr("特定频率"),
                    'file': None,
                    'color': "#FF9800",
                    'volume': 0,
                    'duration': freq_track_duration,
                    'overlay_index': 0
                })

            if max_duration == 0:
                max_duration = 60

            overlay_times = self.main_window.overlay_times.value() if hasattr(self.main_window, 'overlay_times') else 1
            overlay_interval = self.main_window.overlay_interval.value() if hasattr(self.main_window, 'overlay_interval') else 1.0

            if overlay_times > 1 and affirmation_file and os.path.exists(affirmation_file):
                affirmation_duration = self._get_audio_duration(affirmation_file)
                for i in range(1, overlay_times):
                    overlay_start = i * overlay_interval
                    adjusted_duration = max_duration - overlay_start
                    if adjusted_duration > 0:
                        tracks.append({
                            'name': self.main_window.tr("肯定语") + f" ({i+1})",
                            'file': affirmation_file,
                            'color': "#9C27B0",
                            'volume': self.main_window.affirmation_volume.value() if hasattr(self.main_window, 'affirmation_volume') else 0,
                            'duration': min(affirmation_duration, adjusted_duration),
                            'overlay_index': i
                        })

            self._render_tracks(tracks, max_duration)

        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            if hasattr(self.main_window, 'preview_tracks_label'):
                self.main_window.preview_tracks_label.setText(self.main_window.tr(f"预览更新失败: {str(e)}"))

    def _get_audio_duration(self, file_path):
        """获取音频文件时长"""
        try:
            import wave

            if file_path.lower().endswith('.wav'):
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    return frames / float(rate)
            elif file_path.lower().endswith('.mp3'):
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_mp3(file_path)
                    return len(audio) / 1000.0
                except:
                    logger.warning("无法读取MP3文件时长")
                    return 60.0
            else:
                return 60.0
        except Exception as e:
            logger.error(f"获取音频时长失败: {e}")
            return 60.0

    def _render_tracks(self, tracks, max_duration):
        """渲染音轨到预览区域"""
        if not hasattr(self.main_window, 'preview_layout') or not tracks:
            return

        track_height = 40
        max_track_width = 600
        pixels_per_second = max_track_width / max_duration

        for track in tracks:
            track_widget = self._create_track_widget(track, max_duration, pixels_per_second, track_height)
            self.main_window.preview_layout.addWidget(track_widget)

        if hasattr(self.main_window, 'preview_tracks_label'):
            self.main_window.preview_tracks_label.setText(self.main_window.tr("轨道预览"))

    def _create_track_widget(self, track, max_duration, pixels_per_second, track_height):
        """创建单个音轨控件"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
        from PyQt5.QtCore import Qt

        widget = QWidget()
        widget.setFixedHeight(track_height)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        label = QLabel(track['name'])
        label.setFixedWidth(60)
        label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(label)

        track_area = QWidget()
        track_area.setStyleSheet(f"background-color: #f0f0f0; border-radius: 4px;")
        
        clip_width = int(track['duration'] * pixels_per_second)
        clip_width = min(clip_width, int(max_duration * pixels_per_second))
        
        clip = QWidget()
        clip.setFixedWidth(max(clip_width, 5))
        clip.setFixedHeight(track_height - 12)
        clip.setStyleSheet(f"background-color: {track['color']}; border-radius: 3px;")
        
        clip_layout = QHBoxLayout(track_area)
        clip_layout.setContentsMargins(2, 2, 2, 2)
        clip_layout.addWidget(clip)
        
        layout.addWidget(track_area)

        return widget