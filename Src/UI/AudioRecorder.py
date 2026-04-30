from PyQt5.QtCore import QThread, pyqtSignal
import pyaudio
import wave
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

            stream.stop_stream()
            stream.close()
            p.terminate()

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