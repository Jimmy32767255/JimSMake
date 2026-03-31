#!/bin/sh

# SMake 启动脚本 (Linux/macOS)
# 用法:
#   ./Start.sh              - 启动 GUI 模式
#   ./Start.sh -c           - 启动 CLI 模式
#   ./Start.sh --cli        - 启动 CLI 模式

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 检查是否有 CLI 参数
if [ "$1" = "--cli" ] || [ "$1" = "-c" ]; then
    # CLI 模式
    shift  # 移除第一个参数 (--cli 或 -c)
    python ./Src/Main.py --cli "$@"
else
    # GUI 模式 (默认)
    python ./Src/Main.py "$@"
fi
