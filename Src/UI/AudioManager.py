import pyttsx3
import pyaudio
from loguru import logger

class AudioManager:
    """音频管理器 - 处理TTS引擎和音频设备"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def enumerate_tts_engines(self):
        """枚举可用的TTS引擎和语音"""
        logger.debug("开始枚举TTS引擎")
        
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # 清空现有选项
            self.main_window.tts_engine.clear()
            
            # 添加默认选项
            self.main_window.tts_engine.addItem(self.main_window.tr("系统默认"))
            
            seen_names = set()
            
            for voice in voices:
                voice_name = voice.name
                # 清理语音名称
                if 'Microsoft' in voice_name or 'Google' in voice_name:
                    engine_name = voice_name.split('-')[0].strip() if '-' in voice_name else voice_name
                else:
                    engine_name = voice_name
                
                # 去重
                if engine_name in seen_names:
                    continue
                seen_names.add(engine_name)
                
                self.main_window.tts_engine.addItem(engine_name)
                logger.debug(f"添加TTS引擎: {engine_name}")
            
            engine.stop()
            logger.info(f"TTS引擎枚举完成，共找到 {len(voices)} 个语音")
            
        except Exception as e:
            logger.error(f"TTS引擎枚举失败: {e}")
            self.main_window.tts_engine.clear()
            self.main_window.tts_engine.addItem(self.main_window.tr("系统默认"))
            self.main_window.tts_engine.addItem("Microsoft")
            self.main_window.tts_engine.addItem("Google")
            logger.warning("使用默认TTS引擎选项")

    def enumerate_audio_devices(self):
        """枚举系统中可用的音频输入设备"""
        logger.debug("开始枚举音频输入设备")

        try:
            self.main_window.record_device.clear()
            self.main_window.record_device.addItem(self.main_window.tr("系统默认"))

            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            logger.debug(f"系统中共有 {device_count} 个音频设备")

            seen_names = set()

            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)

                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name'].strip()

                    if device_name in seen_names:
                        logger.debug(f"跳过重复设备: {device_name}")
                        continue

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
                    self.main_window.record_device.addItem(device_name, i)
                    logger.debug(f"添加音频输入设备: {device_name} (索引: {i})")

            p.terminate()
            logger.info(f"音频设备枚举完成，共找到 {len(seen_names)} 个输入设备")

        except Exception as e:
            logger.error(f"音频设备枚举失败: {e}")
            self.main_window.record_device.clear()
            self.main_window.record_device.addItem(self.main_window.tr("系统默认"))
            self.main_window.record_device.addItem(self.main_window.tr("麦克风 (Realtek)"))
            logger.warning("使用默认音频设备选项")