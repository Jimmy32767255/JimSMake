# JimSMake - All-in-One Subliminal Audio Production Tool

[简体中文](../README.md) | English

## Project Overview

JimSMake is a professional subliminal audio production tool that provides an intuitive graphical interface and command-line interface to help users easily create subliminal audio content.

[Directory Information](../DirInfo.txt)

[License](../LICENSE)

[To-Do List](../todo.md)

## Social Media

QQ Group: 1095279278

## Related Videos

[Feature Introduction Video](https://www.bilibili.com/video/BV1sKDZBwEEZ)

[Download Tutorial Video](https://www.bilibili.com/video/BV1hkQsBHE61)

[Speed Comparison Video](https://www.bilibili.com/video/BV1VXQgBEEa7)

### Key Features

- **Affirmation Processing** - Supports multiple input methods including audio file import, text-to-speech, and recording
- **Audio Effects** - Volume adjustment, frequency transformation, speed control, and reverse playback
- **Overlay Effects** - Multi-track overlay with adjustable overlay count, intervals, and volume decrement
- **Background Music** - Add background tracks with independent volume control
- **Video Generation** - Combine audio with visualization images to generate video content
- **Image Search** - Integrated search engine for online visualization image search
- **Metadata Management** - Set output file title, author, and other information
- **CLI Support** - Command-line interface for batch processing and automation scripts

## Quick Start

### System Requirements

- Operating System: Windows 11, major Linux distributions
  
- It is strongly recommended that you install [FFmpeg](https://ffmpeg.org/) on your operating system, otherwise you will only be able to use basic features.

**Note**: If you do not install FFmpeg, the following features will not be available:
- Video generation feature
- Import of audio files in non-WAV formats (only WAV format supported)
- Output format selection (only WAV output supported)
- Metadata addition feature

Whether using the packaged version or the interpreted version, FFmpeg is required for advanced features. **The packaged version does not include FFmpeg!**

For the interpreted version, the following additional requirements are needed:

- Python 3.6 or higher
- PyQt5 5.15 or higher

### Installation Steps

#### Packaged Version

**Recommended for regular users**

1. **Download the packaged version**

   Download the latest version of JimSMake from the [Releases](https://github.com/Jimmy32767255/JimSMake/releases/latest) page.

   After downloading, extract the files to your chosen directory.

   Optional: Verify the integrity of the downloaded file (md5/sha256/sha512).

#### Interpreted Execution

If you want to participate in project development or debug/modify the code, you need to download the interpreted version.

*(The interpreted version is only recommended for development, not for regular users)*

1. **Clone the repository**
   
   ```bash
   git clone https://github.com/Jimmy32767255/JimSMake.git
   cd JimSMake
   ```

2. **Install dependencies**

   *(It is recommended to install dependencies in a virtual environment)*

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   
   ```bash
   python -m pip install -r requirements.txt
   ```

   If you encounter issues with missing portaudio.h when installing PyAudio, such as [this issue](https://github.com/Jimmy32767255/JimSMake/issues/1), you can read [this article](https://blog.csdn.net/zhang_zijun2/article/details/159652397) for a solution.

## Usage Guide

### Running the Program
   
   **GUI Mode** (default):
   
   Windows:
   ```bash
   Start.bat
   ```
   
   Linux:
   ```bash
   ./Start.sh
   ```
   
   **CLI Mode**:
   
   Windows:
   ```bash
   Start.bat -c
   ```
   
   Linux:
   ```bash
   ./Start.sh -c
   ```

### GUI Mode

#### Affirmation Settings

1. **Input Method Selection**
   
   - **Audio File**: Directly select an existing audio file
   - **Text Input**: Manually enter affirmation text
   - **Text File**: Import affirmations from a .txt file

2. **TTS Generation**
   
   - Select a TTS engine (TTS engines installed on your system)
   - Click "Generate" to generate speech from text

3. **Recording Function**
   
   - Select a recording device
   - Click "Start Recording" to record affirmations

4. **Audio Effect Adjustment**
   
   - **Volume**: Adjust from -60dB to 0dB
   - **Frequency Mode**:
     - Raw (unchanged)
     - UG (ultrasonic)
     - Traditional (infrasonic/subsonic)
   - **Speed**: 1.0x to 10.0x
   - **Reverse**: Audio plays backwards when enabled

5. **Overlay Effect Settings**
   
   - **Overlay Count**: 1-10 times
   - **Interval Time**: 0-10 seconds
   - **Volume Decrement**: Decrease 0-10dB per overlay

#### Background Audio Settings

- Select background audio file
- Adjust background volume (-60dB to 0dB)

#### Output Settings

1. **Audio Output**
   
   - Format: WAV/MP3
   - Sample Rate: 44.1kHz/48kHz/96kHz/192kHz

2. **Video Output**
   
   - **Visualization Image**: Select local image or search online
   - **Search Engine**: Bing/Google/DuckDuckGo
   - **Video Format**: MP4/AVI/MKV
   - **Audio Sample Rate**: 44.1kHz/48kHz/96kHz
   - **Bitrate**: 128-320 kbps
   - **Resolution**: 360p to 1080p

3. **Metadata**
   
   - Set title and author information

### CLI Mode

CLI mode is suitable for batch processing, automation scripts, or headless environments.

#### Basic Usage

```bash
python -m Src.Main -c [options]
```

Or using the startup script:

```bash
# Windows
Start.bat -c [options]

# Linux
./Start.sh -c [options]
```

#### Complete Example

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
  --title "My Subliminal Audio" \
  --author "Your name"
```

#### CLI Parameters

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `--cli` | `-c` | Launch CLI mode | - |
| `--affirmation` | `-a` | Path to affirmation audio file (WAV format) | Required |
| `--output` | `-o` | Output file path | Required |
| `--background` | `-b` | Path to background audio file (WAV format) | None |
| `--format` | `-f` | Output format (WAV/MP3) | WAV |
| `--volume` | - | Volume adjustment for affirmation (dB) | -23 |
| `--bg-volume` | - | Volume adjustment for background (dB) | 0 |
| `--freq-mode` | - | Frequency mode (0=Raw, 1=UG, 2=Traditional) | 0 |
| `--speed` | - | Playback speed | 1.0 |
| `--reverse` | - | Reverse affirmation playback | False |
| `--overlay-times` | - | Number of overlays | 1 |
| `--overlay-interval` | - | Interval between overlays (seconds) | 1.0 |
| `--volume-decrease` | - | Volume decrease per overlay (dB) | 0.0 |
| `--ensure-integrity` | - | Ensure affirmation integrity | False |
| `--image` | `-v` | Path to visualization image | None |
| `--video` | - | Also generate video | False |
| `--resolution` | - | Video resolution | 1920x1080 |
| `--title` | - | Audio/video title metadata | None |
| `--author` | - | Audio/video author metadata | None |
| `--version` | - | Display version information | - |
| `--help` | `-h` | Display help information | - |

#### Frequency Mode Description

- **0 (Raw)**: Keep original frequency unchanged
- **1 (UG)**: Ultrasonic mode, shifts audio to 17500-20000Hz range
- **2 (Traditional)**: Infrasonic/Subsonic mode, lowers audio to 100-300Hz range

#### Automatic CLI Mode Switching

When GUI fails to start (e.g., missing PyQt5 dependencies), the program will automatically switch to CLI mode. In this case, ensure that the `-a` and `-o` parameters are provided.

## Development Guide

### Packaging

#### Package for Current Operating System on Local Machine

Windows:

```bash
build.bat
```

#### Build AppImage (Linux Universal Package)

```bash
./Build.sh
```

Build output is generated at `./dist/Linux/GNU-Linux-amd64.AppImage`.

#### Package for Other Operating Systems on Local Machine

##### Package for Linux on Windows

Before packaging for Linux on Windows, you need to install [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

1. Enter WSL terminal

2. Change working directory to the SMake repository root

3. Execute `build.sh --wsl`

The `--wsl` parameter uses the venv-wsl virtual environment directory to avoid conflicts with the host's virtual environment

##### Build AppImage on Windows

1. Enter WSL terminal

2. Change working directory to the SMake repository root

3. Same as the above methods for building AppImage on Linux

#### Package Without Using Virtual Environment

Windows:

```bash
build.bat -g
```

The `-g` parameter skips creating or entering a virtual environment and installs dependencies directly to the system global environment (not recommended)

### Internationalization Support

The program includes a translation framework. To add a new language translation:

1. Generate translation files:
   
   ```bash
   pylupdate5 ./Translation/SMake.pro
   ```

2. Use Qt Linguist or manually edit translation files

3. Compile to generate .qm files:
   
   ```bash
   lrelease ./Translation/SMake.pro
   ```

## Contact

If you have questions or suggestions, please contact us through:

- Create an [issue](https://github.com/Jimmy32767255/JimSMake/issues/new)
- Send an email to: Jimmy32767255@outlook.com

---

**If this project is helpful to you, welcome to star it for support!**
