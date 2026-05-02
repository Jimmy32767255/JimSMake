# CLI Mode

[Back](../Readme/en-US.md)

CLI mode is suitable for batch processing, automation scripts, or environments without a graphical interface.

## Basic Usage

```bash
python -m Src.Main -c [options]
```

Or using the startup scripts:

```bash
# Windows
Start.bat -c [options]

# Linux
Start.sh -c [options]
```

## Complete Example

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

## CLI Parameters

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `--cli` | `-c` | Enable CLI mode | - |
| `--affirmation` | `-a` | Affirmation audio file path (WAV format) | Required |
| `--output` | `-o` | Output file path | Required |
| `--background` | `-b` | Background music file path (WAV format) | None |
| `--format` | `-f` | Output format (WAV/MP3) | WAV |
| `--volume` | - | Affirmation volume adjustment (dB) | -23 |
| `--bg-volume` | - | Background volume adjustment (dB) | 0 |
| `--freq-mode` | - | Frequency mode (0=Raw, 1=UG, 2=Traditional) | 0 |
| `--speed` | - | Playback speed | 1.0 |
| `--reverse` | - | Reverse affirmation audio | False |
| `--overlay-times` | - | Number of overlays | 1 |
| `--overlay-interval` | - | Overlay interval (seconds) | 1.0 |
| `--volume-decrease` | - | Volume decrease per overlay (dB) | 0.0 |
| `--ensure-integrity` | - | Ensure affirmation integrity | False |
| `--image` | `-v` | Visualization image path | None |
| `--video` | - | Generate video simultaneously | False |
| `--resolution` | - | Video resolution | 1920x1080 |
| `--title` | - | Audio/Video title metadata | None |
| `--author` | - | Audio/Video author metadata | None |
| `--version` | - | Show version information | - |
| `--help` | `-h` | Show help information | - |

## Frequency Modes

- **0 (Raw)**: Keep original frequency unchanged
- **1 (UG)**: Ultra-sonic mode, shifts audio to 17500-20000Hz range
- **2 (Traditional)**: Infrasonic mode, lowers audio to 100-300Hz range

## Automatic CLI Mode Switching

When GUI startup fails (e.g., missing PyQt5 dependency), the program will automatically switch to CLI mode. In this case, ensure that the `-a` and `-o` parameters are provided.
