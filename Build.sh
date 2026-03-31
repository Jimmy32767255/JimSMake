#!/bin/bash

# SMake 打包脚本 (Linux/macOS)
# 用法: ./build.sh [选项]
#
# 选项:
#   --wsl    使用 venv-wsl 虚拟环境（用于在 WSL 中打包）
#   -g       跳过虚拟环境，使用系统全局 Python（不建议）

set -e

echo "=========================================="
echo "SMake 打包工具"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 解析参数
USE_WSL=false
USE_GLOBAL=false
VENV_DIR="venv"

while [[ $# -gt 0 ]]; do
    case $1 in
        --wsl)
            USE_WSL=true
            VENV_DIR="venv-wsl"
            shift
            ;;
        -g)
            USE_GLOBAL=true
            shift
            ;;
        *)
            echo "[警告] 未知参数: $1"
            shift
            ;;
    esac
done

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python3"
    exit 1
fi

# 处理虚拟环境
if [ "$USE_GLOBAL" = true ]; then
    echo "[信息] 使用系统全局 Python（-g 模式）"
elif [ "$USE_WSL" = true ]; then
    echo "[信息] WSL 模式，使用 $VENV_DIR 虚拟环境"
    if [ -d "$VENV_DIR" ]; then
        echo "[信息] 激活虚拟环境..."
        source "$VENV_DIR/bin/activate"
    else
        echo "[信息] 创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi
else
    # 默认使用 venv
    if [ -d "$VENV_DIR" ]; then
        echo "[信息] 激活虚拟环境..."
        source "$VENV_DIR/bin/activate"
    else
        echo "[信息] 创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi
fi

# 安装/更新依赖
echo "[信息] 安装依赖..."
pip install -r requirements.txt -q

# 安装 PyInstaller
echo "[信息] 安装 PyInstaller..."
pip install pyinstaller -q

# 清理本次构建的临时目录（只清理 build，保留 dist）
echo "[信息] 清理临时构建目录..."
rm -rf build

# 执行打包
echo "[信息] 开始打包..."
pyinstaller Build.spec --clean

# 退出虚拟环境

if [ "$USE_GLOBAL" = false ]; then
    echo "[信息] 退出虚拟环境..."
    deactivate
fi

# 创建平台专属目录并移动打包结果
OUTPUT_DIR="dist/Linux"
echo "[信息] 创建输出目录: $OUTPUT_DIR..."
mkdir -p "$OUTPUT_DIR"

# 移动打包结果到平台专属目录
if [ -d "dist/SMake" ]; then
    mv dist/SMake/* "$OUTPUT_DIR/"
    rmdir dist/SMake
elif [ -f "dist/SMake" ]; then
    mv dist/SMake "$OUTPUT_DIR/"
fi

# 复制额外文件到输出目录
echo "[信息] 复制资源文件..."
if [ -d "Translation" ]; then
    cp -r Translation "$OUTPUT_DIR/"
fi

# 创建启动脚本
echo "[信息] 创建启动脚本..."
cat > "$OUTPUT_DIR/Start.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
./SMake "$@"
EOF
chmod +x "$OUTPUT_DIR/Start.sh"

echo "=========================================="
echo "[成功] 打包完成！"
echo "输出目录: $OUTPUT_DIR/"
echo "可执行文件: $OUTPUT_DIR/SMake"
echo "=========================================="
