# AGENTS.md

## 项目概述

JimSMake 是一款专业的潜意识音频制作工具，提供图形界面（GUI）和命令行界面（CLI）。

- **许可证**：GPL v3
- **主要语言**：Python 3.6+
- **依赖**：FFmpeg（强烈建议安装）
- **框架**：PyQt5（GUI）

## 代码结构

请参阅[目录信息](DirInfo.txt)

## 开发规范

### Python 开发

- 使用虚拟环境（venv）
- 遵循 PEP 8 风格
- 安装依赖：`pip install -r requirements.txt`
- 运行测试：`pytest`

### 提交更改

- 创建 Pull Request 到 `Dev` 分支，**不要**直接提交到 `main`
- 使用清晰的提交信息前缀：`feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- 确保测试已覆盖并通过

### 代码原则

- 保持简单，避免过度工程化
- 不要为一次性操作创建抽象
- 仅在系统边界（用户输入、外部 API）处添加验证
- 信任内部代码和框架保证
- 不要添加未请求的额外功能或配置

## 常见任务

### 添加新音频效果

修改 `Src/Processors/AudioCore.py` 和 `Src/Processors/AudioProcessor.py`。

### 添加测试

在 `Tests/unit/` 或 `Tests/integration/` 下添加测试文件，以 `test_` 开头。

具体请参阅 `pytest.ini` 中的测试文件命名模式定义

### 更新翻译

请参阅[国际化支持文档](Docs/Translation/zh-CN.md)

**特别注意：** 如果添加了新的用户界面控件，请在 `Src/UI/Main_Window.py` 的 `retranslateUI` 方法中添加对应的处理逻辑，否则翻译无法正常生效！

## 注意事项

- GUI 和 CLI 功能需要保持同步
- 音频处理重度依赖 FFmpeg，处理前检查其可用性
