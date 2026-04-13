# JimSMake - 一站式潜意识音频制作工具

## 项目简介

JimSMake 是一款专业的潜意识音频制作工具，提供直观的图形界面和命令行界面，帮助用户轻松创建潜意识音频内容。

### 主要特性

- **肯定语处理** - 支持音频文件导入、文本转语音、录制等多种输入方式
- **音频效果** - 音量调节、频率变换、倍速控制、倒放功能
- **叠加效果** - 支持多轨叠加，可调节叠加次数、间隔和音量递减
- **背景音乐** - 添加背景音轨，独立控制音量
- **视频生成** - 将音频与视觉化图片结合，生成视频内容
- **图片搜索** - 集成搜索引擎，在线搜索视觉化图片
- **元数据管理** - 设置输出文件的标题、作者等信息
- **CLI 支持** - 命令行界面，支持批量处理和自动化脚本

## 快速开始

### 系统要求

- 操作系统：Windows 11、Linux主要发行版
  
- *注意我们不保证除 Arch Linux 以外的 GNU/Linux 发行版可以正常运行*
  
- 您还需要在您的操作系统中安装 [FFmpeg](https://ffmpeg.org/) 。

对于解释执行版本则需要以下额外条件：

- Python 3.6 或更高版本
- PyQt5 5.15 或更高版本

### 安装步骤

#### 打包版本

1. **下载打包版本**

   从 [Releases](https://github.com/Jimmy32767255/JimSMake/releases/latest) 页面下载最新版本的 JimSMake。

   下载完成后，解压文件到您选择的目录。

   可选：校验下载的文件是否完整（md5/sha256/sha512）。

#### 解释执行（建议用于开发）

1. **克隆仓库**
   
   ```bash
   git clone https://github.com/Jimmy32767255/JimSMake.git
   cd JimSMake
   ```

2. **安装依赖**

   *（建议您在虚拟环境中安装依赖）*

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   
   ```bash
   python -m pip install -r requirements.txt
   ```

   如果您在安装 PyAudio 时遇到了缺失 portaudio.h 头文件的问题，例如[这个问题](https://github.com/Jimmy32767255/JimSMake/issues/1)，可以阅读[这篇文章](https://blog.csdn.net/zhang_zijun2/article/details/159652397)解决。

## 使用指南

### 运行程序
   
   **GUI 模式** (默认):
   
   Windows：
   ```bash
   Start.bat
   ```
   
   Linux：
   ```bash
   ./Start.sh
   ```
   
   **CLI 模式**:
   
   Windows：
   ```bash
   Start.bat -c
   ```
   
   Linux：
   ```bash
   ./Start.sh -c
   ```

### GUI 模式

#### 肯定语设置

1. **输入方式选择**
   
   - **音频文件**：直接选择已有的音频文件
   - **文本输入**：手动输入肯定语文本
   - **文本文件**：从 .txt 文件导入肯定语

2. **TTS生成**
   
   - 选择 TTS 引擎（系统中已安装的 TTS 引擎）
   - 点击"生成"按钮，从文本生成语音

3. **录音功能**
   
   - 选择录音设备
   - 点击"开始录制"录制肯定语

4. **音频效果调节**
   
   - **音量**：-60dB 到 0dB 调节
   - **频率模式**：
     - Raw（保持不变）
     - UG（亚超声波）
     - 传统（次声波）
   - **倍速**：1.0x 到 10.0x
   - **倒放**：开启后音频反向播放

5. **叠加效果设置**
   
   - **叠加次数**：1-10次
   - **间隔时间**：0-10秒
   - **音量递减**：每次叠加降低 0-10dB

#### 背景音设置

- 选择背景音频文件
- 调节背景音量（-60dB 到 0dB）

#### 输出设置

1. **音频输出**
   
   - 格式：WAV/MP3
   - 采样率：44.1kHz/48kHz/96kHz/192kHz

2. **视频输出**
   
   - **视觉化图片**：选择本地图片或在线搜索
   - **搜索引擎**：Bing/Google/DuckDuckGo
   - **视频格式**：MP4/AVI/MKV
   - **音频采样率**：44.1kHz/48kHz/96kHz
   - **码率**：128-320 kbps
   - **分辨率**：360p 到 1080p

3. **元数据**
   
   - 设置标题和作者信息

### CLI 模式

CLI 模式适用于批量处理、自动化脚本或无图形界面环境。

#### 基本用法

```bash
python -m Src.Main -c [选项]
```

或使用启动脚本：

```bash
# Windows
Start.bat -c [选项]

# Linux
./Start.sh -c [选项]
```

#### 完整示例

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

#### CLI 参数说明

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

#### 频率模式说明

- **0 (Raw)**：保持不变，原始频率
- **1 (UG)**：亚超声波模式，将音频搬移到 17500-20000Hz 范围
- **2 (传统)**：次声波模式，将音频降低到 100-300Hz 范围

#### 自动切换 CLI 模式

当 GUI 启动失败时（如缺少 PyQt5 依赖），程序会自动切换到 CLI 模式。此时需要确保已提供 `-a` 和 `-o` 参数。

## 开发指南

### 打包

#### 在本地计算机上为当前操作系统打包

Windows：

```bash
build.bat
```

Linux：

```bash
build.sh
```

#### 在本地计算机上为其它操作系统打包

##### 在 Windows 上为 Linux 打包

在 Windows 上为 Linux 打包前，需要先安装 [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

1. 进入 WSL 终端

2. 切换工作目录为 SMake 仓库根目录

3. 执行 `build.sh --wsl`

`--wsl` 参数会使用 venv-wsl 虚拟环境目录，以避免与宿主机的虚拟环境冲突

##### 在 Linux 上为 Windows 打包

在 Linux 上为 Windows 打包前需要先安装 [Wine](https://www.winehq.org/)

1. 进入 Wine CMD

2. 切换工作目录为 SMake 仓库根目录

3. 执行 `build.bat --wine`

`--wine` 参数会使用 venv-wine 虚拟环境目录，以避免与宿主机的虚拟环境冲突

#### 不使用虚拟环境进行打包

Linux：

```bash
build.sh -g
```

Windows：

```bash
build.bat -g
```

`-g` 参数会跳过创建或进入虚拟环境，直接安装依赖到系统全局（不建议这样做）

### 国际化支持

程序内置了翻译支持框架。要添加新语言的翻译：

1. 生成翻译文件：
   
   ```bash
   pylupdate5 ./Translation/SMake.pro
   ```

2. 使用 Qt Linguist 或手动编辑翻译文件

3. 编译生成 .qm 文件：
   
   ```bash
   lrelease ./Translation/SMake.pro
   ```

## 许可证

本项目采用 GPLv3 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

如有问题或建议，请通过以下方式联系我们：

- 创建一个[议题](https://github.com/Jimmy32767255/JimSMake/issues/new)
- 发送邮件至：Jimmy32767255@outlook.com

---

**如果这个项目对您有帮助，欢迎star支持！**
