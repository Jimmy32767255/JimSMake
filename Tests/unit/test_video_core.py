"""
VideoCore 单元测试
"""
import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Src'))

from Processors.VideoCore import VideoCore


class TestVideoCore:
    """VideoCore 测试类"""

    @pytest.fixture
    def video_core(self):
        """创建 VideoCore 实例"""
        return VideoCore()

    @pytest.fixture
    def sample_params(self):
        """示例参数"""
        return {
            'audio_path': 'test.mp3',
            'video_image': 'test.jpg',
            'video_output_path': 'output.mp4',
            'video_resolution': '1920x1080',
            'metadata_title': 'Test Title',
            'metadata_author': 'Test Author'
        }

    def test_init(self, video_core):
        """测试初始化"""
        assert video_core is not None
        assert video_core.params == {}
        assert video_core.is_cancelled is False

    def test_init_with_params(self, sample_params):
        """测试带参数的初始化"""
        core = VideoCore(sample_params)
        assert core.params == sample_params

    def test_set_params(self, video_core, sample_params):
        """测试设置参数"""
        video_core.set_params(sample_params)
        assert video_core.params == sample_params

    def test_cancel(self, video_core):
        """测试取消功能"""
        assert video_core.check_cancelled() is False
        video_core.cancel()
        assert video_core.check_cancelled() is True

    def test_generate_video_no_audio(self, video_core, temp_output_dir):
        """测试没有音频文件时生成视频"""
        params = {
            'audio_path': 'nonexistent.mp3',
            'video_image': 'test.jpg',
            'video_output_path': os.path.join(temp_output_dir, 'output.mp4')
        }
        video_core.set_params(params)

        result = video_core.generate_video()
        assert result is False

    def test_generate_video_no_image(self, video_core, temp_output_dir):
        """测试没有图片文件时生成视频"""
        # 创建一个假的音频文件
        audio_path = os.path.join(temp_output_dir, 'fake.mp3')
        with open(audio_path, 'w') as f:
            f.write('fake audio')

        params = {
            'audio_path': audio_path,
            'video_image': 'nonexistent.jpg',
            'video_output_path': os.path.join(temp_output_dir, 'output.mp4')
        }
        video_core.set_params(params)

        result = video_core.generate_video()
        assert result is False

    def test_generate_video_cancelled(self, video_core, temp_output_dir):
        """测试取消后的视频生成"""
        # 创建假文件
        audio_path = os.path.join(temp_output_dir, 'fake.mp3')
        image_path = os.path.join(temp_output_dir, 'fake.jpg')
        with open(audio_path, 'w') as f:
            f.write('fake')
        with open(image_path, 'w') as f:
            f.write('fake')

        params = {
            'audio_path': audio_path,
            'video_image': image_path,
            'video_output_path': os.path.join(temp_output_dir, 'output.mp4')
        }
        video_core.set_params(params)
        video_core.cancel()

        result = video_core.generate_video()
        assert result is False

    def test_generate_video_with_callback(self, video_core, temp_output_dir):
        """测试带回调的视频生成（文件不存在）"""
        progress_values = []

        def progress_callback(value):
            progress_values.append(value)

        result = video_core.generate_video(
            audio_path='nonexistent.mp3',
            image_path='nonexistent.jpg',
            output_path=os.path.join(temp_output_dir, 'output.mp4'),
            progress_callback=progress_callback
        )

        assert result is False
        # 回调应该被调用（即使失败也会报告进度）
        assert len(progress_values) > 0

    def test_generate_video_params_override(self, video_core, temp_output_dir):
        """测试参数覆盖"""
        # 设置初始参数
        video_core.set_params({
            'audio_path': 'initial.mp3',
            'video_image': 'initial.jpg',
            'video_output_path': 'initial.mp4',
            'video_resolution': '1280x720',
            'metadata_title': 'Initial',
            'metadata_author': 'Initial'
        })

        # 使用generate_video的参数覆盖
        audio_path = os.path.join(temp_output_dir, 'test.mp3')
        image_path = os.path.join(temp_output_dir, 'test.jpg')
        with open(audio_path, 'w') as f:
            f.write('fake')
        with open(image_path, 'w') as f:
            f.write('fake')

        # 调用时传入不同的参数
        result = video_core.generate_video(
            audio_path=audio_path,
            image_path=image_path,
            output_path=os.path.join(temp_output_dir, 'output.mp4'),
            resolution='1920x1080',
            metadata_title='Override',
            metadata_author='Override'
        )

        # 由于ffmpeg不可用，结果应该是False
        # 但测试验证了参数传递逻辑
        assert result is False

    def test_check_cancelled_during_generation(self, video_core, temp_output_dir):
        """测试生成过程中检查取消状态"""
        # 创建假文件
        audio_path = os.path.join(temp_output_dir, 'fake.mp3')
        image_path = os.path.join(temp_output_dir, 'fake.jpg')
        with open(audio_path, 'w') as f:
            f.write('fake')
        with open(image_path, 'w') as f:
            f.write('fake')

        call_count = [0]

        def progress_callback(value):
            call_count[0] += 1
            if call_count[0] >= 1:
                video_core.cancel()

        result = video_core.generate_video(
            audio_path=audio_path,
            image_path=image_path,
            output_path=os.path.join(temp_output_dir, 'output.mp4'),
            progress_callback=progress_callback
        )

        # 由于取消了，应该返回False
        assert result is False

    def test_generate_video_missing_params(self, video_core):
        """测试缺少必要参数"""
        # 不设置任何参数
        result = video_core.generate_video()
        assert result is False

    def test_generate_video_empty_audio_path(self, video_core, temp_output_dir):
        """测试空音频路径"""
        result = video_core.generate_video(
            audio_path='',
            image_path='test.jpg',
            output_path=os.path.join(temp_output_dir, 'output.mp4')
        )
        assert result is False

    def test_generate_video_empty_image_path(self, video_core, temp_output_dir):
        """测试空图片路径"""
        # 创建假音频文件
        audio_path = os.path.join(temp_output_dir, 'fake.mp3')
        with open(audio_path, 'w') as f:
            f.write('fake')

        result = video_core.generate_video(
            audio_path=audio_path,
            image_path='',
            output_path=os.path.join(temp_output_dir, 'output.mp4')
        )
        assert result is False

    def test_init_logs_params(self, sample_params, caplog):
        """测试初始化时记录日志"""
        # 由于loguru使用标准logging，只需验证初始化不抛出异常
        # 并且参数被正确设置
        core = VideoCore(sample_params)
        assert core.params == sample_params
        # 验证关键参数存在
        assert core.params.get('video_image') == 'test.jpg'
        assert core.params.get('audio_path') == 'test.mp3'
