import os
import json
from loguru import logger
from PyQt5.QtCore import QUrl

class PreviewManager:
    """预览管理器 - 处理音频预览和时间轴显示（使用WebView实现）"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.web_view = None
        self.preview_page_loaded = False

    def setup_web_view(self, web_view):
        """设置WebView引用"""
        self.web_view = web_view
        # 加载本地HTML文件
        preview_html_path = os.path.join(
            os.path.dirname(__file__), 'WebPreview', 'index.html'
        )
        if os.path.exists(preview_html_path):
            self.web_view.loadFinished.connect(self._on_page_loaded)
            self.web_view.setUrl(QUrl.fromLocalFile(preview_html_path))
            logger.debug(f"加载预览页面: {preview_html_path}")
        else:
            logger.error(f"预览页面不存在: {preview_html_path}")

    def _on_page_loaded(self, ok):
        """页面加载完成回调"""
        self.preview_page_loaded = ok
        if ok:
            logger.debug("预览页面加载完成")
            # 页面加载完成后立即更新一次预览
            self.update_preview()
        else:
            logger.error("预览页面加载失败")

    def update_preview(self):
        """更新预览视图"""
        logger.debug("开始更新预览")

        if not self.web_view or not self.preview_page_loaded:
            logger.debug("WebView未就绪，跳过预览更新")
            return

        affirmation_file = self.main_window.affirmation_file.text() if hasattr(self.main_window, 'affirmation_file') else ""
        background_file = self.main_window.background_file.text() if hasattr(self.main_window, 'background_file') else ""

        if not affirmation_file and not background_file:
            self._clear_preview()
            return

        try:
            tracks = []
            max_duration = 0

            # 获取背景音频时长
            if background_file and os.path.exists(background_file):
                bg_duration = self._get_audio_duration(background_file)
                max_duration = bg_duration
                tracks.append({
                    'name': self.main_window.tr("背景音乐"),
                    'file': background_file,
                    'color': "#4CAF50",
                    'volume': self.main_window.background_volume.value() if hasattr(self.main_window, 'background_volume') else 0,
                    'duration': bg_duration,
                    'overlayIndex': 0,
                    'overlayInterval': 0,
                    'isLoop': False
                })

            # 获取肯定语音频时长
            affirmation_duration = 0
            if affirmation_file and os.path.exists(affirmation_file):
                affirmation_duration = self._get_audio_duration(affirmation_file)

            # 检查是否启用"确保完整性"模式
            ensure_integrity = False
            if hasattr(self.main_window, 'ensure_integrity_check'):
                ensure_integrity = self.main_window.ensure_integrity_check.isChecked()

            # 获取叠加设置
            overlay_times = self.main_window.overlay_times.value() if hasattr(self.main_window, 'overlay_times') else 1
            overlay_interval = self.main_window.overlay_interval.value() if hasattr(self.main_window, 'overlay_interval') else 0.0

            # 计算肯定语的实际播放方式
            if affirmation_file and os.path.exists(affirmation_file):
                if max_duration == 0:
                    # 没有背景音乐，只显示肯定语本身
                    max_duration = affirmation_duration
                    tracks.append({
                        'name': self.main_window.tr("肯定语"),
                        'file': affirmation_file,
                        'color': "#2196F3",
                        'volume': self.main_window.affirmation_volume.value() if hasattr(self.main_window, 'affirmation_volume') else 0,
                        'duration': affirmation_duration,
                        'overlayIndex': 0,
                        'overlayInterval': 0,
                        'isLoop': False
                    })
                else:
                    # 有背景音乐
                    if ensure_integrity:
                        # 确保完整性模式：肯定语完整循环播放，填满背景音频
                        # 计算完整循环次数
                        full_cycles = int(max_duration // affirmation_duration)
                        remaining = max_duration % affirmation_duration

                        # 添加完整循环的片段
                        for i in range(full_cycles):
                            tracks.append({
                                'name': self.main_window.tr("肯定语") if i == 0 else self.main_window.tr("肯定语") + f" (循环{i+1})",
                                'file': affirmation_file,
                                'color': "#2196F3" if i == 0 else "#64B5F6",
                                'volume': self.main_window.affirmation_volume.value() if hasattr(self.main_window, 'affirmation_volume') else 0,
                                'duration': affirmation_duration,
                                'overlayIndex': i,
                                'overlayInterval': affirmation_duration,
                                'isLoop': True
                            })

                        # 确保完整性模式下，不完整的剩余部分不会添加肯定语
                        # 只添加完整循环的片段，不添加部分片段
                    else:
                        # 普通模式：肯定语循环重复填满背景音频
                        # 计算需要多少个循环才能填满背景音频
                        loop_count = int(max_duration / affirmation_duration) + (1 if max_duration % affirmation_duration > 0 else 0)

                        for i in range(loop_count):
                            start_time = i * affirmation_duration
                            remaining_duration = max_duration - start_time
                            actual_duration = min(affirmation_duration, remaining_duration)

                            if actual_duration > 0.1:
                                tracks.append({
                                    'name': self.main_window.tr("肯定语") if i == 0 else self.main_window.tr("肯定语") + f" (循环{i+1})",
                                    'file': affirmation_file,
                                    'color': "#2196F3" if i == 0 else "#64B5F6",
                                    'volume': self.main_window.affirmation_volume.value() if hasattr(self.main_window, 'affirmation_volume') else 0,
                                    'duration': actual_duration,
                                    'overlayIndex': i,
                                    'overlayInterval': affirmation_duration,
                                    'isLoop': True
                                })

            # 添加叠加的肯定语音轨
            if overlay_times > 1 and affirmation_file and os.path.exists(affirmation_file):
                for i in range(1, overlay_times):
                    overlay_start = i * overlay_interval

                    if overlay_start < max_duration:
                        # 计算这个叠加轨道的实际播放时长
                        if ensure_integrity:
                            # 确保完整性模式
                            available_duration = max_duration - overlay_start
                            full_cycles = int(available_duration // affirmation_duration)
                            remaining = available_duration % affirmation_duration

                            for j in range(full_cycles):
                                tracks.append({
                                    'name': self.main_window.tr("肯定语") + f" (叠加{i+1}循环{j+1})",
                                    'file': affirmation_file,
                                    'color': "#9C27B0",
                                    'volume': self.main_window.affirmation_volume.value() if hasattr(self.main_window, 'affirmation_volume') else 0,
                                    'duration': affirmation_duration,
                                    'overlayIndex': i,
                                    'overlayInterval': overlay_interval,
                                    'loopOffset': j * affirmation_duration,
                                    'isLoop': True
                                })

                            # 确保完整性模式下，不完整的剩余部分不会添加肯定语
                        else:
                            # 普通模式：循环填满
                            available_duration = max_duration - overlay_start
                            loop_count = int(available_duration / affirmation_duration) + (1 if available_duration % affirmation_duration > 0 else 0)

                            for j in range(loop_count):
                                loop_start = overlay_start + j * affirmation_duration
                                remaining = max_duration - loop_start
                                actual_duration = min(affirmation_duration, remaining)

                                if actual_duration > 0.1:
                                    tracks.append({
                                        'name': self.main_window.tr("肯定语") + f" (叠加{i+1}循环{j+1})",
                                        'file': affirmation_file,
                                        'color': "#9C27B0" if j == 0 else "#AB47BC",
                                        'volume': self.main_window.affirmation_volume.value() if hasattr(self.main_window, 'affirmation_volume') else 0,
                                        'duration': actual_duration,
                                        'overlayIndex': i,
                                        'overlayInterval': overlay_interval,
                                        'loopOffset': j * affirmation_duration,
                                        'isLoop': True
                                    })

            # 添加特定频率音轨
            if hasattr(self.main_window, 'freq_track_enabled') and self.main_window.freq_track_enabled.isChecked():
                freq_track_duration = max_duration if max_duration > 0 else 60
                tracks.append({
                    'name': self.main_window.tr("特定频率"),
                    'file': None,
                    'color': "#FF9800",
                    'volume': self.main_window.freq_track_volume.value() if hasattr(self.main_window, 'freq_track_volume') else 0,
                    'duration': freq_track_duration,
                    'overlayIndex': 0,
                    'overlayInterval': 0,
                    'isLoop': False
                })

            if max_duration == 0:
                max_duration = 60

            self._send_preview_data(tracks, max_duration)

        except Exception as e:
            logger.error(f"更新预览失败: {e}")

    def _clear_preview(self):
        """清空预览"""
        if self.web_view and self.preview_page_loaded:
            js_code = "if (window.clearAudioPreview) { window.clearAudioPreview(); }"
            self.web_view.page().runJavaScript(js_code)

    def _send_preview_data(self, tracks, max_duration):
        """发送预览数据到WebView"""
        if not self.web_view or not self.preview_page_loaded:
            return

        # 构建预览数据
        preview_data = {
            'tracks': tracks,
            'maxDuration': max_duration
        }

        # 将数据转换为JSON并传递给JavaScript
        json_data = json.dumps(preview_data, ensure_ascii=False)
        js_code = f"""
            if (window.updateAudioPreview) {{
                const data = {json_data};
                window.updateAudioPreview(data.tracks, data.maxDuration);
            }}
        """
        self.web_view.page().runJavaScript(js_code)
        logger.debug(f"预览数据已发送: {len(tracks)} 个轨道, 总时长 {max_duration:.1f}s")

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

    # 保留原有方法以保持兼容性（但不再使用PyQt5渲染）
    def preview_zoom_in(self):
        """放大预览视图（已废弃，保留兼容性）"""
        logger.debug("Web预览不支持缩放操作")

    def preview_zoom_out(self):
        """缩小预览视图（已废弃，保留兼容性）"""
        logger.debug("Web预览不支持缩放操作")

    def preview_reset(self):
        """重置预览视图（已废弃，保留兼容性）"""
        logger.debug("Web预览不支持重置操作")

    def _apply_preview_zoom(self):
        """应用预览缩放（已废弃，保留兼容性）"""
        pass

    def _render_tracks(self, tracks, max_duration):
        """渲染音轨到预览区域（已废弃，保留兼容性）"""
        pass

    def _create_track_widget(self, track, max_duration, pixels_per_second, track_height):
        """创建单个音轨控件（已废弃，保留兼容性）"""
        pass
