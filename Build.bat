@echo off
chcp 65001 >nul

REM SMake 打包脚本 (Windows)
REM 用法: build.bat [选项]
REM
REM 选项:
REM   --wine   使用 venv-wine 虚拟环境（用于在 Wine 中打包）
REM   -g       跳过虚拟环境，使用系统全局 Python（不建议）

echo ==========================================
echo SMake 打包工具
echo ==========================================

REM 初始化变量
set "USE_WINE=false"
set "USE_GLOBAL=false"
set "VENV_DIR=venv"

REM 解析参数
:parse_args
if "%~1"=="" goto :done_parsing
if "%~1"=="--wine" (
    set "USE_WINE=true"
    set "VENV_DIR=venv-wine"
    shift
    goto :parse_args
)
if "%~1"=="-g" (
    set "USE_GLOBAL=true"
    shift
    goto :parse_args
)
echo [警告] 未知参数: %~1
shift
goto :parse_args
:done_parsing

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 处理虚拟环境
if "%USE_GLOBAL%"=="true" (
    echo [信息] 使用系统全局 Python（-g 模式）
    goto :skip_venv
)

if "%USE_WINE%"=="true" (
    echo [信息] Wine 模式，使用 %VENV_DIR% 虚拟环境
) else (
    echo [信息] 使用 %VENV_DIR% 虚拟环境
)

if exist "%VENV_DIR%" (
    echo [信息] 激活虚拟环境...
    call %VENV_DIR%\Scripts\activate.bat
) else (
    echo [信息] 创建虚拟环境...
    python -m venv %VENV_DIR%
    call %VENV_DIR%\Scripts\activate.bat
)

:skip_venv

REM 安装/更新依赖
echo [信息] 安装依赖...
pip install -r requirements.txt -q

REM 安装 PyInstaller
echo [信息] 安装 PyInstaller...
pip install pyinstaller -q

REM 清理本次构建的临时目录（只清理 build，保留 dist）
echo [信息] 清理临时构建目录...
if exist "build" rmdir /s /q build

REM 执行打包
echo [信息] 开始打包...
pyinstaller Build.spec --clean

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

REM 退出虚拟环境

if "%USE_GLOBAL%"=="false" (
    call %VENV_DIR%\Scripts\deactivate.bat
    echo [信息] 退出虚拟环境...
)

REM 创建平台专属目录并移动打包结果
set "OUTPUT_DIR=dist\Windows"
echo [信息] 创建输出目录: %OUTPUT_DIR%...
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 移动打包结果到平台专属目录
if exist "dist\SMake" (
    move /y "dist\SMake.exe" "%OUTPUT_DIR%\SMake.exe" >nul 2>&1
    move /y "dist\SMake\*" "%OUTPUT_DIR%\" >nul 2>&1
    rmdir /s /q "dist\SMake"
)

REM 复制额外文件到输出目录
echo [信息] 复制资源文件...
if exist "Translation" xcopy /s /i /y "Translation" "%OUTPUT_DIR%\Translation" >nul

REM 创建启动脚本
echo [信息] 创建启动脚本...
echo @echo off > "%OUTPUT_DIR%\Start.bat"
echo SMake.exe >> "%OUTPUT_DIR%\Start.bat"

echo ==========================================
echo [成功] 打包完成！
echo 输出目录: %OUTPUT_DIR%\
echo 可执行文件: %OUTPUT_DIR%\SMake.exe
echo ==========================================
