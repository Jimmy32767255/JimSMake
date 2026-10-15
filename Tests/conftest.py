"""
PyTest 全局配置和共享fixtures
"""
import pytest
import sys
import os

# 添加Src目录到Python路径（使用规范化绝对路径，避免出现 ".." 片段）
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Src'))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)


@pytest.fixture(scope="session")
def test_data_dir():
    """返回测试数据目录路径"""
    return os.path.join(os.path.dirname(__file__), 'data')


@pytest.fixture(scope="function")
def temp_output_dir(tmp_path):
    """创建临时输出目录"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def mock_audio_params():
    """返回标准音频参数"""
    return {
        'affirmation_file': '',
        'background_file': '',
        'output_path': '',
        'volume': 0.0,
        'speed': 1.0,
        'reverse': False,
        'overlay_times': 1,
        'overlay_interval': 1.0,
        'volume_decrease': 0.0,
        'overlay_stagger_mode': False,
        'background_volume': 0.0,
        'freq_track_enabled': False,
        'isochronic_enabled': False,
        'output_format': 'WAV'
    }
