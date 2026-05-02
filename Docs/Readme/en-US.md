# JimSMake - One-Stop Subliminal Audio Production Tool

[简体中文](../../README.md) | English

## Introduction

JimSMake is a professional subliminal audio production tool that provides an intuitive graphical interface and command-line interface, helping users easily create subliminal audio content.

[Directory Info](../../DirInfo.txt)

[License](../../LICENSE)

[Todos](../../todo.md)

## Social Media

QQ Group: 1095279278

## Related Videos

[Feature Introduction Video](https://www.bilibili.com/video/BV1sKDZBwEEZ)

[Download Tutorial Video](https://www.bilibili.com/video/BV1hkQsBHE61)

[Speed Comparison Video](https://www.bilibili.com/video/BV1VXQgBEEa7)

### Key Features

- **Affirmation Processing** - Supports audio file import, text-to-speech, recording, and more
- **Audio Effects** - Volume adjustment, frequency shifting, speed control, reverse playback
- **Overlay Effects** - Multi-track overlay with adjustable count, interval, and volume decrease
- **Background Music** - Add background tracks with independent volume control
- **Video Generation** - Combine audio with visualization images to create videos
- **Image Search** - Integrated search engines for online visualization images
- **Metadata Management** - Set title, author, and other output file information
- **CLI Support** - Command-line interface for batch processing and automation scripts

## Quick Start

### System Requirements

- OS: Windows 11, Major Linux distributions

- It is strongly recommended to install [FFmpeg](https://ffmpeg.org/) on your system, otherwise you will only be able to use basic features.

**Note**: Without FFmpeg installed, the following features will be unavailable:
- Video generation
- Importing non-WAV audio files (WAV only)
- Output format selection (WAV only)
- Metadata functionality

Both packaged and source versions require FFmpeg for advanced features. **The packaged version does not include FFmpeg!**

For the source version, additional requirements:

- Python 3.6 or higher

### Installation

#### Packaged Version

**Recommended for regular users**

1. **Download the Packaged Version**

   Download the latest JimSMake release from the [Releases](https://github.com/Jimmy32767255/JimSMake/releases/latest) page.

   After downloading, extract the archive to your chosen directory.

   Optional: Verify file integrity (md5/sha1/sha256/sha512).

#### Source Installation

If you want to participate in development or debug/modify the code, you need the source version.

*(Source version is recommended for development only, not for regular users)*

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Jimmy32767255/JimSMake.git
   cd JimSMake
   ```

2. **Install Dependencies**

   *(It is recommended to install dependencies in a virtual environment)*

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   ```bash
   python -m pip install -r requirements.txt
   ```

   If you encounter missing portaudio.h header file issues when installing PyAudio, such as [this issue](https://github.com/Jimmy32767255/JimSMake/issues/1), you can refer to [this article](https://blog.csdn.net/zhang_zijun2/article/details/159652397) for a solution.

## Usage Guide

### Running the Program

   **GUI Mode** (default):

   Windows:
   ```bash
   Start.bat
   ```

   Linux:
   ```bash
   Start.sh
   ```

   **CLI Mode**:

   Windows:
   ```bash
   Start.bat -c
   ```

   Linux:
   ```bash
   Start.sh -c
   ```

### GUI Mode

#### Affirmation Settings

1. **Input Method Selection**

   - **Audio File**: Select an existing audio file directly
   - **Text Input**: Manually enter affirmation text
   - **Text File**: Import affirmations from a .txt file

2. **TTS Generation**

   - Select a TTS engine (installed on your system)
   - Click the "Generate" button to create speech from text

3. **Recording**

   - Select a recording device
   - Click "Start Recording" to record affirmations

4. **Audio Effects**

   - **Volume**: Adjust from -60dB to 0dB
   - **Frequency Mode**:
     - Raw (keep original)
     - UG (Ultra-sonic)
     - Traditional (Infrasonic)
   - **Speed**: 1.0x to 10.0x
   - **Reverse**: Play audio in reverse when enabled

5. **Overlay Effects**

   - **Overlay Count**: 1-10 times
   - **Interval**: 0-10 seconds
   - **Volume Decrease**: 0-10dB reduction per overlay

#### Background Music Settings

- Select a background audio file
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

CLI mode is suitable for batch processing, automation scripts, or environments without a graphical interface.

For detailed documentation, please refer to the [CLI Mode Documentation](../CLI/en-US.md).

## Development Guide

### Build

For detailed documentation, please refer to the [Build Guide](../Build/en-US.md).

### Internationalization

The program includes a translation framework. To add a new language translation:

1. Generate translation files:

   ```bash
   pylupdate5 ./Translation/SMake.pro
   ```

2. Use Qt Linguist or manually edit the translation files

3. Compile to generate .qm files:

   ```bash
   lrelease ./Translation/SMake.pro
   ```

## Contact

For questions or suggestions, please contact us through:

- Create an [Issue](https://github.com/Jimmy32767255/JimSMake/issues/new)
- Email: Jimmy32767255@outlook.com
- Join the QQ Group: 1095279278
- Via [Online Form](https://docs.qq.com/sheet/DYURpZFBCVkNYSWVh?tab=BB08J2)

---

**If this project helps you, feel free to star it!**
