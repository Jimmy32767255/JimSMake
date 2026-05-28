# JimSMake - One-Stop Subliminal Audio Production Tool

[简体中文](../../README.md) | English

## Introduction

![SMake](../../Assets/SMakeIcon256.png)

JimSMake is a professional subliminal audio production tool that provides an intuitive graphical interface and command-line interface, helping users easily create subliminal audio content.

[Directory Info](../../DirInfo.txt)

[License](../../LICENSE)

[Todos](../../todo.md)

### Social Media

QQ Group: 1095279278

### Related Videos

[Feature Introduction Video](https://www.bilibili.com/video/BV1sKDZBwEEZ)

[Download Tutorial Video](https://www.bilibili.com/video/BV1hkQsBHE61)

[Speed Comparison Video](https://www.bilibili.com/video/BV1VXQgBEEa7)

### Key Features

- **Project Group** - Support creating and managing multiple project groups for organizing different types of audio production tasks
- **Import/Export** - Support .zip and .tar.xz format project import/export for easy backup and sharing
- **Batch Processing** - Support multi-project batch generation to improve work efficiency
- **Affirmation Processing** - Supports audio file import, text-to-speech (TTS), microphone recording, and more
- **Audio Effects** - Volume adjustment (dB), frequency shifting (e.g. 17500Hz), speed control, reverse playback
- **Overlay Effects** - Multi-track overlay with adjustable count, interval, volume decrease, and stagger mode (normal/reverse alternation)
- **Background Music** - Add background tracks with independent volume control
- **Specific Frequency Overlay** - Support 432/639/1111Hz and other specific frequency track overlay, with difference mode and channel inversion
- **Video Generation** - Combine audio with visualization images to create MP4 and other video formats
- **Image Search** - Integrated search engines for online visualization image search
- **Metadata Management** - Set title, author, and other ID3 tag information for output files
- **Output File Management** - Automatically organize output files into audio/video directories with timestamp naming
- **Decompilation** - Reverse-engineer affirmations from output audio for safety review (respect copyright, do not use for illegal purposes)
- **Multi-language Interface** - Support Simplified Chinese, American English, and other language switching
- **CLI Support** - Full command-line support for use in environments without a graphical interface

## Quick Start

### Tips

It is recommended to develop the good habit of proactively checking for updates. Check back periodically for new releases, as they will include new features and bug fixes!

*Automatic update checking is planned*

The Dev branch has more cutting-edge features. If you are capable, you can download and try it yourself. However, the Dev branch does not provide precompiled versions and does not accept feedback.

Older versions are not supported. Please make sure you are using the latest version before reporting any issues!

If you need to use an older version, please download the documentation for that version. The documentation is only updated with the latest version, so it may not apply to older versions.

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
   - **Stagger Mode**: When enabled, overlay tracks will alternate between normal and reversed playback. The first track plays normally, the second reversed, the third normally, and so on

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

For detailed documentation, please refer to the [Translation Guide](../Translation/en-US.md).

## Contact

For questions or suggestions, please contact us through:

- Create an [Issue](https://github.com/Jimmy32767255/JimSMake/issues/new)
- Email: Jimmy32767255@outlook.com
- Join the QQ Group: 1095279278
- Via [Online Form](https://docs.qq.com/sheet/DYURpZFBCVkNYSWVh?tab=BB08J2)

---

**If this project helps you, feel free to star it!**
