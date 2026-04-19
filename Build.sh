#!/bin/bash

# JimSMake AppImage 构建脚本 (使用 appimagetool)
# 用法: ./BuildAppImage.sh

set -e

echo "=========================================="
echo "JimSMake AppImage 构建工具 (appimagetool)"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 创建构建目录
BUILD_DIR="$SCRIPT_DIR/build-appimage"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# 检查依赖
echo "[检查依赖...]"

# 检查 appimagetool
if [[ ! -f "appimagetool-x86_64.AppImage" ]]; then
    echo "[下载 appimagetool...]"
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# 检查 runtime
if [[ ! -f "runtime-x86_64" ]]; then
    echo "[下载 AppImage runtime...]"
    wget -q "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64"
fi

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python3"
    exit 1
fi

echo "[依赖检查完成]"

# 创建 AppDir 结构
echo "[创建 AppDir 结构...]"
APPDIR="$BUILD_DIR/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/share/jimsmake"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/pixmaps"
mkdir -p "$APPDIR/usr/lib"

# 复制程序文件
echo "[复制程序文件...]"
cp -r "$SCRIPT_DIR/Src" "$APPDIR/usr/share/jimsmake/"
cp -r "$SCRIPT_DIR/Assets" "$APPDIR/usr/share/jimsmake/"
cp -r "$SCRIPT_DIR/Translation" "$APPDIR/usr/share/jimsmake/"

# 安装 Python 依赖到 AppDir
echo "[安装 Python 依赖...]"
pip3 install --prefix="$APPDIR/usr" -r "$SCRIPT_DIR/requirements.txt"

# 复制图标
cp "$SCRIPT_DIR/Assets/SMakeIcon256.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/jimsmake.png"
cp "$SCRIPT_DIR/Assets/SMakeIcon256.png" "$APPDIR/usr/share/pixmaps/jimsmake.png"

# 创建桌面文件
cat > "$APPDIR/usr/share/applications/jimsmake.desktop" << 'EOF'
[Desktop Entry]
Name=JimSMake
Comment=一站式潜意识音频制作工具
Exec=jimsmake
Icon=jimsmake
Terminal=false
Type=Application
Categories=Utility
StartupNotify=true
EOF

# 创建启动脚本
cat > "$APPDIR/usr/bin/jimsmake" << 'EOF'
#!/bin/bash
# JimSMake 启动脚本

HERE="$(dirname "$(readlink -f "${0}")")"
APPDIR="$(dirname "$(dirname "$HERE")")"

# 查找 Python site-packages 目录
PYTHON_VERSION=$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')
export PYTHONPATH="$APPDIR/usr/share/jimsmake:$APPDIR/usr/lib/$PYTHON_VERSION/site-packages:$PYTHONPATH"

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "警告: 未检测到 FFmpeg，请确保已安装 FFmpeg"
    echo "您可以通过包管理器安装:"
    echo "  sudo apt install ffmpeg (Debian/Ubuntu)"
    echo "  sudo pacman -S ffmpeg (Arch Linux)"
    echo "  sudo dnf install ffmpeg (Fedora)"
fi

exec python3 "$APPDIR/usr/share/jimsmake/Src/Main.py" "$@"
EOF
chmod +x "$APPDIR/usr/bin/jimsmake"

# 创建 AppRun 脚本
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
# AppImage 入口点

# 获取 AppDir 路径
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# 设置环境变量
export PATH="$HERE/usr/bin:$PATH"

# 查找 Python site-packages 目录
PYTHON_VERSION=$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')
export PYTHONPATH="$HERE/usr/share/jimsmake:$HERE/usr/lib/$PYTHON_VERSION/site-packages:$PYTHONPATH"

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "警告: 未检测到 FFmpeg，请确保已安装 FFmpeg"
    echo "您可以通过包管理器安装:"
    echo "  sudo apt install ffmpeg (Debian/Ubuntu)"
    echo "  sudo pacman -S ffmpeg (Arch Linux)"
    echo "  sudo dnf install ffmpeg (Fedora)"
fi

# 启动程序
exec python3 "$HERE/usr/share/jimsmake/Src/Main.py" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# 复制 .desktop 到根目录
cp "$APPDIR/usr/share/applications/jimsmake.desktop" "$APPDIR/jimsmake.desktop"

# 复制图标到根目录
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/jimsmake.png" "$APPDIR/jimsmake.png"

# 使用 appimagetool 打包
echo "[使用 appimagetool 打包...]"
./appimagetool-x86_64.AppImage "$APPDIR" --runtime-file runtime-x86_64

# 检查并提示
cd "$SCRIPT_DIR"
if [[ -f "$BUILD_DIR/JimSMake-x86_64.AppImage" ]]; then
    mkdir -p "$SCRIPT_DIR/dist/Linux"
    mv "$BUILD_DIR/JimSMake-x86_64.AppImage" "$SCRIPT_DIR/dist/Linux/GNU-Linux-amd64.AppImage"
    echo ""
    echo "=========================================="
    echo "构建成功!"
    echo "=========================================="
    echo "输出文件: $SCRIPT_DIR/dist/Linux/GNU-Linux-amd64.AppImage"
    echo ""
    echo "注意: 运行前请确保已安装 FFmpeg"
    echo "  sudo apt install ffmpeg (Debian/Ubuntu)"
    echo "  sudo pacman -S ffmpeg (Arch Linux)"
    echo "  sudo dnf install ffmpeg (Fedora)"
    echo "=========================================="
else
    echo "[错误] 构建失败，未找到输出文件"
    exit 1
fi
