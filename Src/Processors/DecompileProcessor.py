from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from loguru import logger
import os
import tempfile
import subprocess
from .DecompileCore import DecompileCore


class DecompileProcessor(QThread, DecompileCore):
    """音频反编译处理线程 - 处理音频反编译 (GUI版本)"""
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    processing_error = pyqtSignal(str)
    preview_ready = pyqtSignal(object)  # 预览音频数据准备好

    def __init__(self, params):
        QThread.__init__(self)
        DecompileCore.__init__(self, params)
        self.mode = 'export'  # 'export' 或 'preview'
        self.audio_info = None  # 用于预览的音频数据
        logger.debug(f"DecompileProcessor初始化 - 参数: {params}")

    def set_mode(self, mode):
        """设置处理模式"""
        self.mode = mode  # 'export' 或 'preview'

    def set_audio_info(self, audio_info):
        """设置音频数据（用于预览）"""
        self.audio_info = audio_info

    def run(self):
        """执行反编译处理"""
        try:
            if self.mode == 'preview':
                self._run_preview()
            else:
                self._run_export()
        except Exception as e:
            logger.error(f"反编译处理出错: {e}")
            self.processing_error.emit(str(e))

    def _run_preview(self):
        """运行预览生成"""
        logger.info("开始生成反编译预览")

        def progress_callback(progress):
            self.progress_updated.emit(progress)

        result = self.generate_preview(self.audio_info, self.params, progress_callback)

        if result:
            logger.debug("预览生成成功")
            self.preview_ready.emit(result)
        else:
            logger.error("预览生成失败")
            self.processing_error.emit(self.tr("生成预览失败"))

    def _run_export(self):
        """运行导出处理"""
        logger.info("开始反编译导出")

        def progress_callback(progress):
            self.progress_updated.emit(progress)

        result = self.process(progress_callback=progress_callback)

        if result:
            logger.debug(f"反编译成功，输出路径: {result}")
            self.processing_finished.emit(result)
        else:
            logger.error("反编译失败")
            self.processing_error.emit(self.tr("导出音频文件失败"))


class DecompilePlayer(QThread):
    """反编译音频播放器线程 - 使用临时文件方式播放"""
    position_changed = pyqtSignal(int)  # 播放位置变化（毫秒）
    duration_changed = pyqtSignal(int)  # 总时长变化（毫秒）
    playback_finished = pyqtSignal()
    playback_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.audio_info = None
        self.temp_file = None
        self.sample_rate = 44100
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.duration_ms = 0
        self.volume = 1.0
        self._process = None  # 播放进程
        self._timer = None  # 位置更新定时器

    def set_audio(self, audio_info):
        """设置要播放的音频数据"""
        if audio_info:
            self.audio_info = audio_info
            self.sample_rate = audio_info['sample_rate']
            self.duration_ms = int(len(audio_info['data']) / self.sample_rate * 1000)
            self.duration_changed.emit(self.duration_ms)
            self.current_position = 0
            # 清理之前的临时文件
            self._cleanup_temp_file()
            # 创建新的临时文件
            self._create_temp_file()

    def _create_temp_file(self):
        """创建临时音频文件"""
        if not self.audio_info:
            return
        try:
            # 创建临时WAV文件
            fd, self.temp_file = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            # 使用 DecompileCore 的 save_audio 方法保存
            from .DecompileCore import DecompileCore
            core = DecompileCore({})
            core.save_audio(self.audio_info, self.temp_file)
            logger.debug(f"临时音频文件已创建: {self.temp_file}")
        except Exception as e:
            logger.error(f"创建临时音频文件失败: {e}")
            self.temp_file = None

    def _cleanup_temp_file(self):
        """清理临时文件"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                logger.debug(f"临时音频文件已删除: {self.temp_file}")
            except Exception as e:
                logger.warning(f"删除临时音频文件失败: {e}")
            self.temp_file = None

    def play(self):
        """开始播放"""
        if not self.is_playing:
            self.is_playing = True
            self.is_paused = False
            self.start()
        elif self.is_paused:
            self.is_paused = False
            # 恢复播放
            self._start_playback()

    def pause(self):
        """暂停播放"""
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self._stop_playback()

    def stop(self):
        """停止播放"""
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self._stop_playback()
        if self._timer:
            self._timer.stop()
        self.position_changed.emit(0)

    def seek(self, position_ms):
        """跳转到指定位置（毫秒）"""
        self.current_position = max(0, min(position_ms, self.duration_ms))
        if self.is_playing and not self.is_paused:
            # 重新播放
            self._stop_playback()
            self._start_playback()

    def set_volume(self, volume):
        """设置音量 (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))

    def _start_playback(self):
        """开始播放音频"""
        if not self.temp_file or not os.path.exists(self.temp_file):
            self.playback_error.emit("临时音频文件不存在")
            return

        try:
            # 使用 ffplay 播放音频（支持精确控制）
            ffmpeg_path = self._get_ffmpeg_path()
            if ffmpeg_path:
                ffplay_path = ffmpeg_path.replace('ffmpeg', 'ffplay')
                if os.path.exists(ffplay_path):
                    # 计算起始位置（秒）
                    start_sec = self.current_position / 1000.0
                    cmd = [
                        ffplay_path,
                        '-nodisp',  # 不显示窗口
                        '-autoexit',  # 播放完自动退出
                        '-ss', str(start_sec),  # 起始位置
                        '-volume', str(int(self.volume * 100)),  # 音量
                        self.temp_file
                    ]
                    self._process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    logger.debug(f"开始播放: {self.temp_file} 从 {start_sec}s 开始")
                else:
                    # 使用系统默认播放器
                    self._play_with_default_player()
            else:
                # 使用系统默认播放器
                self._play_with_default_player()

            # 启动位置更新定时器
            if not self._timer:
                from PyQt5.QtCore import QTimer
                self._timer = QTimer()
                self._timer.timeout.connect(self._update_position)
            self._timer.start(100)  # 每100ms更新一次位置

        except Exception as e:
            logger.error(f"播放失败: {e}")
            self.playback_error.emit(f"播放失败: {str(e)}")

    def _stop_playback(self):
        """停止播放"""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=1)
            except:
                try:
                    self._process.kill()
                except:
                    pass
            self._process = None

    def _play_with_default_player(self):
        """使用系统默认播放器"""
        try:
            if os.name == 'posix':  # Linux/macOS
                self._process = subprocess.Popen(
                    ['xdg-open', self.temp_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:  # Windows
                import winsound
                winsound.PlaySound(self.temp_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            logger.error(f"使用默认播放器失败: {e}")
            raise

    def _get_ffmpeg_path(self):
        """获取 ffmpeg 路径"""
        try:
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _update_position(self):
        """更新播放位置"""
        if self.is_playing and not self.is_paused:
            self.current_position += 100  # 增加100ms
            if self.current_position >= self.duration_ms:
                self.current_position = self.duration_ms
                self.is_playing = False
                self.playback_finished.emit()
                if self._timer:
                    self._timer.stop()
            self.position_changed.emit(self.current_position)

    def run(self):
        """播放线程"""
        try:
            if not self.audio_info:
                self.playback_error.emit("没有音频数据")
                return

            if not self.temp_file:
                self.playback_error.emit("临时音频文件创建失败")
                return

            # 开始播放
            self._start_playback()

            # 等待播放完成
            while self.is_playing:
                self.msleep(100)
                if self._process:
                    ret = self._process.poll()
                    if ret is not None and not self.is_paused:
                        # 播放完成
                        if self.current_position >= self.duration_ms - 500:  # 允许500ms误差
                            self.playback_finished.emit()
                        break

        except Exception as e:
            import traceback
            error_detail = f"播放错误: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_detail)
            self.playback_error.emit(str(e))
        finally:
            self.is_playing = False
            self._stop_playback()

    def __del__(self):
        """析构时清理"""
        self._cleanup_temp_file()
