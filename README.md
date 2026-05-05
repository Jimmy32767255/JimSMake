# JimSMake - 一站式潜意识音频制作工具

简体中文 | [English](Docs/Readme/en-US.md)

## 项目简介

JimSMake 是一款专业的潜意识音频制作工具，提供直观的图形界面和命令行界面，帮助用户轻松创建潜意识音频内容。

[目录信息](DirInfo.txt)

[许可证](LICENSE)

[待办事项](todo.md)

## 社交媒体

QQ 交流群：1095279278

## 相关视频

[功能介绍视频](https://www.bilibili.com/video/BV1sKDZBwEEZ)

[下载教程视频](https://www.bilibili.com/video/BV1hkQsBHE61)

[速度对比视频](https://www.bilibili.com/video/BV1VXQgBEEa7)

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

- 操作系统：Windows 11、Linux 主要发行版
  
- 强烈建议您在您的操作系统中安装 [FFmpeg](https://ffmpeg.org/) ，否则您将只能使用基础功能。

**注意**：如果您未安装 FFmpeg，以下功能将无法使用：
- 视频生成功能
- 非 WAV 格式的音频文件导入（仅支持 WAV 格式）
- 输出格式选择（仅支持输出 WAV 格式）
- 元数据添加功能

无论是打包版本还是解释执行版本，使用高级功能都需要安装FFmpeg，**打包版本不包含FFmpeg！**

对于解释执行版本则需要以下额外条件：

- Python 3.6 或更高版本

### 安装步骤

#### 打包版本

**推荐普通用户使用此方式**

1. **下载打包版本**

   从 [Releases](https://github.com/Jimmy32767255/JimSMake/releases/latest) 页面下载最新版本的 JimSMake。

   下载完成后，解压文件到您选择的目录。

   可选：校验下载的文件是否完整（md5/sha1/sha256/sha512）。

#### 解释执行

如果您想要参与项目开发或进行调试/修改，您需要下载解释执行版本。

*（解释执行版本仅建议用于开发，不推荐普通用户使用）*

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
   Start.sh
   ```
   
   **CLI 模式**:
   
   Windows：
   ```bash
   Start.bat -c
   ```
   
   Linux：
   ```bash
   Start.sh -c
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

详细说明请参阅 [CLI 模式文档](Docs/CLI/zh-CN.md)。

## 开发指南

### 打包

详细说明请参阅 [打包指南](Docs/Build/zh-CN.md)。

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

## 联系方式

如有问题或建议，请通过以下方式联系我们：

- 创建一个[议题](https://github.com/Jimmy32767255/JimSMake/issues/new)
- 发送邮件至：Jimmy32767255@outlook.com
- 添加QQ交流群聊：1095279278
- 通过[在线表格](https://docs.qq.com/sheet/DYURpZFBCVkNYSWVh?tab=BB08J2)

---

**如果这个项目对您有帮助，欢迎star支持！**
