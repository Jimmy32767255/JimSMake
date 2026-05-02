# CLI 模式

[返回](../../README.md)

CLI 模式适用于批量处理、自动化脚本或无图形界面环境。

## 基本用法

```bash
python -m Src.Main -c [选项]
```

或使用启动脚本：

```bash
# Windows
Start.bat -c [选项]

# Linux
Start.sh -c [选项]
```

## 完整示例

```bash
python -m Src.Main -c \
  -a ./Project/My_Project/Assets/Affirmation/Microsoft_Huihui_zh-CN.wav \
  -b ./Project/My_Project/Assets/BGM.wav \
  -o ./Project/My_Project/Releases.mp3 \
  -f MP3 \
  --freq-mode 1 \
  --speed 3.5 \
  --overlay-times 3 \
  --overlay-interval 2.0 \
  --volume-decrease 5.0 \
  --ensure-integrity \
  -v ./Project/My_Project/Assets/Visualization.png \
  --video \
  --title "我的潜意识音频" \
  --author "Your name"
```

## CLI 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--cli` | `-c` | 启动 CLI 模式 | - |
| `--affirmation` | `-a` | 肯定语音频文件路径 (WAV格式) | 必填 |
| `--output` | `-o` | 输出文件路径 | 必填 |
| `--background` | `-b` | 背景音文件路径 (WAV格式) | 无 |
| `--format` | `-f` | 输出格式 (WAV/MP3) | WAV |
| `--volume` | - | 肯定语音量调整 (dB) | -23 |
| `--bg-volume` | - | 背景音量调整 (dB) | 0 |
| `--freq-mode` | - | 频率模式 (0=Raw, 1=UG, 2=传统) | 0 |
| `--speed` | - | 倍速 | 1.0 |
| `--reverse` | - | 倒放肯定语 | False |
| `--overlay-times` | - | 叠加次数 | 1 |
| `--overlay-interval` | - | 叠加间隔 (秒) | 1.0 |
| `--volume-decrease` | - | 每次叠加音量递减 (dB) | 0.0 |
| `--ensure-integrity` | - | 确保肯定语完整性 | False |
| `--image` | `-v` | 视觉化图片路径 | 无 |
| `--video` | - | 同时生成视频 | False |
| `--resolution` | - | 视频分辨率 | 1920x1080 |
| `--title` | - | 音频/视频标题元数据 | 无 |
| `--author` | - | 音频/视频作者元数据 | 无 |
| `--version` | - | 显示版本信息 | - |
| `--help` | `-h` | 显示帮助信息 | - |

## 频率模式说明

- **0 (Raw)**：保持不变，原始频率
- **1 (UG)**：亚超声波模式，将音频搬移到 17500-20000Hz 范围
- **2 (传统)**：次声波模式，将音频降低到 100-300Hz 范围

## 自动切换 CLI 模式

当 GUI 启动失败时（如缺少 PyQt5 依赖），程序会自动切换到 CLI 模式。此时需要确保已提供 `-a` 和 `-o` 参数。
