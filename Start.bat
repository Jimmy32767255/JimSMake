@echo off
chcp 65001 >nul

REM SMake 启动脚本 (Windows)
REM 用法:
REM   Start.bat              - 启动 GUI 模式
REM   Start.bat -c        - 启动 CLI 模式
REM   Start.bat --cli        - 启动 CLI 模式

setlocal enabledelayedexpansion

REM 获取脚本所在目录
cd /d "%~dp0"

REM 检查第一个参数
set "FIRST_ARG=%~1"

if /I "!FIRST_ARG!"=="--cli" goto :cli_mode
if /I "!FIRST_ARG!"=="-c" goto :cli_mode

REM GUI 模式 (默认)
python .\Src\Main.py %*
goto :end

:cli_mode
REM CLI 模式
shift
python .\Src\Main.py --cli %*

:end
endlocal
