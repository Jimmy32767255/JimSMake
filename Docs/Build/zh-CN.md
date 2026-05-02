# 打包指南

[返回](../../README.md)

## 在本地计算机上为当前操作系统打包

Windows：

```bash
build.bat
```

## 构建 AppImage (Linux 通用包)

```bash
Build.sh
```

构建产物生成于 `./dist/Linux/GNU-Linux-amd64.AppImage` 。

## 在本地计算机上为其它操作系统打包

### 在 Windows 上为 Linux 打包

在 Windows 上为 Linux 打包前，需要先安装 [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

1. 进入 WSL 终端

2. 切换工作目录为 SMake 仓库根目录

3. 执行 `build.sh --wsl`

`--wsl` 参数会使用 venv-wsl 虚拟环境目录，以避免与宿主机的虚拟环境冲突

### 在 Windows 上构建 AppImage 包

1. 进入 WSL 终端

2. 切换工作目录为 SMake 仓库根目录

3. 与上述 Linux 上构建 AppImage 包相同。

### 在 Linux 上为 Windows 打包

在 Linux 上为 Windows 打包前需要先安装 [Wine](https://www.winehq.org/)

1. 进入 Wine CMD

2. 切换工作目录为 SMake 仓库根目录

3. 执行 `build.bat --wine`

`--wine` 参数会使用 venv-wine 虚拟环境目录，以避免与宿主机的虚拟环境冲突

## 不使用虚拟环境进行打包

Windows：

```bash
build.bat -g
```

`-g` 参数会跳过创建或进入虚拟环境，直接安装依赖到系统全局（不建议这样做）
