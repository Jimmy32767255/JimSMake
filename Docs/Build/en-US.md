# Build Guide

[Back](../Readme/en-US.md)

## Build for Current Operating System

Windows:

```bash
build.bat
```

## Build AppImage (Linux Universal Package)

```bash
Build.sh
```

The build artifact is generated at `./dist/Linux/GNU-Linux-amd64.AppImage`.

## Cross-Platform Builds

### Build for Linux on Windows

Before building for Linux on Windows, you need to install [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

1. Enter the WSL terminal

2. Change to the SMake repository root directory

3. Run `build.sh --wsl`

The `--wsl` parameter uses the venv-wsl virtual environment directory to avoid conflicts with the host's virtual environment.

### Build AppImage on Windows

1. Enter the WSL terminal

2. Change to the SMake repository root directory

3. Same as building AppImage on Linux above.

### Build for Windows on Linux

Before building for Windows on Linux, you need to install [Wine](https://www.winehq.org/)

1. Enter Wine CMD

2. Change to the SMake repository root directory

3. Run `build.bat --wine`

The `--wine` parameter uses the venv-wine virtual environment directory to avoid conflicts with the host's virtual environment.

## Build Without Virtual Environment

Windows:

```bash
build.bat -g
```

The `-g` parameter skips creating or entering a virtual environment and installs dependencies globally (not recommended).
