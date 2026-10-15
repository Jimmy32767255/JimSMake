"""
路径处理净化回归测试

背景：Src/ 与 Src/UI/ 目录没有 __init__.py，属于 PEP 420 命名空间包，
其 __path__ 会随 sys.path 的变化重新计算。一旦向 sys.path 插入带 ".."
的路径（例如 <repo>/Src/UI/..），之后导入的模块 __file__ 就会带上冗余的
".." 片段，并进一步污染项目目录、配置文件路径等所有派生路径。
"""
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

# 添加Src目录到路径（规范化绝对路径，避免出现 ".." 片段）
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Src'))
_REPO_ROOT = os.path.dirname(_SRC_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)


def _has_parent_segment(path):
    """路径中是否包含 ".." 片段"""
    return '..' in path.replace('\\', '/').split('/')


def _is_clean(path):
    """路径为绝对路径、已规范化，且不包含 ".." 片段"""
    return (
        os.path.isabs(path)
        and os.path.normpath(path) == path
        and not _has_parent_segment(path)
    )


class TestResourcePath:
    """资源路径规范化测试"""

    def test_get_resource_path_is_clean(self):
        """Main.get_resource_path 返回规范化后的绝对路径"""
        from Main import get_resource_path

        resource_path = get_resource_path()

        assert _is_clean(resource_path)
        assert resource_path == _REPO_ROOT

    def test_main_window_resource_path_is_repo_root(self, monkeypatch):
        """MainWindow.get_resource_path（开发模式）指向仓库根目录"""
        pytest.importorskip('PyQt5.QtWidgets')
        from UI.Main_Window import MainWindow

        # 强制走开发模式分支（避免打包分支）
        monkeypatch.delenv('APPIMAGE', raising=False)
        monkeypatch.delattr(sys, 'frozen', raising=False)

        resource_path = MainWindow.get_resource_path(None)

        assert _is_clean(resource_path)
        assert resource_path == _REPO_ROOT

    def test_project_base_dir_is_clean(self, monkeypatch):
        """项目基础目录不包含 ".." 片段（即使资源路径本身不规范）"""
        pytest.importorskip('PyQt5.QtWidgets')
        from UI.Main_Window import MainWindow

        # 强制走开发模式分支（避免 AppImage / PyInstaller 分支）
        monkeypatch.delenv('APPIMAGE', raising=False)
        monkeypatch.delattr(sys, 'frozen', raising=False)

        dirty_resource = os.path.join(os.sep, 'tmp', 'dummy', '..', 'dummy2')
        stub = SimpleNamespace(get_resource_path=lambda: dirty_resource)

        project_base = MainWindow.get_project_base_dir(stub)

        assert _is_clean(project_base)
        assert project_base == os.path.abspath(os.path.join(dirty_resource, 'Project'))


class TestModuleImportPaths:
    """导入链路上各模块文件路径不包含 ".." 片段"""

    _CHECK_CODE = """
import sys
sys.path.insert(0, {src!r})
import UI.Main_Window as main_window
import UI.ProjectManager as project_manager
import Cli
import Src.Processors.AudioCore as audio_core

for name, module in [
    ('UI.Main_Window', main_window),
    ('UI.ProjectManager', project_manager),
    ('Cli', Cli),
    ('Src.Processors.AudioCore', audio_core),
]:
    print('MODULE=' + name + '|' + module.__file__)
print('DIR=' + main_window._SRC_DIR)
print('DIR=' + Cli._REPO_ROOT)
print('SYSPATH=' + '|'.join(p for p in sys.path if p))
"""

    def test_import_chain_has_no_parent_segments(self):
        """导入 UI.Main_Window 后，后续导入的模块路径依然干净"""
        env = dict(os.environ)
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['PYTHONIOENCODING'] = 'utf-8'

        result = subprocess.run(
            [sys.executable, '-c', self._CHECK_CODE.format(src=_SRC_DIR)],
            cwd=_REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, result.stderr

        module_paths = []
        directory_paths = []
        sys_path_entries = []
        for line in result.stdout.splitlines():
            if line.startswith('MODULE='):
                module_paths.append(line.split('=', 1)[1].split('|', 1)[1])
            elif line.startswith('DIR='):
                directory_paths.append(line.split('=', 1)[1])
            elif line.startswith('SYSPATH='):
                sys_path_entries.extend(line.split('=', 1)[1].split('|'))

        assert len(module_paths) == 4
        assert len(directory_paths) == 2

        for path in module_paths + directory_paths:
            assert _is_clean(path), f"路径未被规范化: {path}"

        for entry in sys_path_entries:
            assert not _has_parent_segment(entry), f"sys.path 含有 \"..\" 片段: {entry}"
