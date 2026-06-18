# 贡献指南

感谢您对 JimSMake 项目的关注！我们欢迎各种形式的贡献，包括但不限于：

- 报告问题
- 提交功能建议
- 改进文档
- 修复错误
- 添加新功能
- 改进翻译
- 改进测试

## 开始之前

- 请确保您已阅读 [README.md](README.md) 了解项目基本信息。
- 请确保您已阅读 [行为准则](CODE_OF_CONDUCT.md)。
- 如果您不确定某个改动是否受欢迎，请先开一个议题（Issue）进行讨论。

## 如何贡献

### 报告问题

如果您发现了错误或有功能建议，请通过 GitHub Issues 提交。

提交问题时，请尽可能提供以下信息：

- 问题的清晰描述
- 复现步骤（如果是错误）
- 期望的行为和实际的行为
- 截图（如果适用）
- 运行环境信息（操作系统、Python 版本等）
- 相关的日志或错误信息

### 提交代码

1. **Fork 仓库**

   点击 GitHub 页面右上角的 "Fork" 按钮，将仓库复制到您的账户下。

2. **克隆您的 Fork**

   ```bash
   git clone https://github.com/JIMMY32767255/JimSMake.git
   cd JimSMake
   ```

3. **创建分支**

   从 `Dev` 分支创建一个新的功能分支：

   ```bash
   git checkout -b feat/your-feature-name
   ```

   分支命名建议：
   - `feat/` - 新功能
   - `fix/` - 错误修复
   - `docs/` - 文档更新
   - `refactor/` - 代码重构
   - `test/` - 测试相关

4. **进行更改**

   - 编写清晰、可读的代码
   - 遵循项目中现有的代码风格
   - 添加或更新必要的测试
   - 更新相关文档

5. **运行测试**

   ```bash
   pytest
   ```

6. **提交更改**

   使用清晰、描述性的提交信息：

   ```bash
   git add .
   git commit -m "feat: 添加某某功能"
   ```

   提交信息格式建议：
   - `feat:` 新功能
   - `fix:` 错误修复
   - `docs:` 文档更新
   - `style:` 代码格式调整（不影响功能）
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建过程或辅助工具的变动

7. **推送到您的 Fork**

   ```bash
   git push origin feat/your-feature-name
   ```

8. **创建 Pull Request**

   在 GitHub 上向 `Dev` 分支创建 Pull Request，并填写 PR 模板中的相关信息。

## 开发环境设置

### 要求

- Python 3.6 或更高版本
- 建议安装 [FFmpeg](https://ffmpeg.org/)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行项目

```bash
python Src/Main.py
```

## 代码风格

- 遵循 PEP 8 风格指南
- 使用有意义的变量名和函数名
- 为复杂逻辑添加注释
- 保持代码简洁，避免过度工程化

## 测试

- 为新功能添加测试
- 确保所有测试在提交前通过
- 测试文件位于 `Tests/` 目录下

## 文档

- 如果更改会影响用户的使用方式，请更新相关文档
- 文档位于 `Docs/` 目录下
- 支持简体中文和英文两种语言

## 翻译贡献

请参阅[国际化支持文档](Docs/Translation/zh-CN.md)

## 问题或需要帮助？

- 加入 QQ 交流群：1095279278
- 在 GitHub Discussions 中提问
- 发送邮件至 [Jimmy32767255@outlook.com](mailto:Jimmy32767255@outlook.com)

再次感谢您的贡献！
