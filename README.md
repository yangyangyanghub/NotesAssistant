<div align="right">
  <a href="#notesassistant-中文">中文</a> | <a href="#notesassistant">English</a>
</div>

# NotesAssistant

## Project Introduction

NotesAssistant is an AI-based personal knowledge base management tool focused on solving content export and management issues for closed systems like WeChat Favorites. By combining Claude Code and MCP (Model Context Protocol) technology, it enables intelligent desktop application control, providing users with an efficient and secure knowledge management solution.

## Key Features

- **WeChat Favorites Export**：Automatically batch export WeChat Favorites content, including screenshots, text, and metadata
- **Long Content Processing**：Support scroll-spliced long screenshots to ensure complete capture of long articles
- **Intelligent Recognition**：Automatically identify UI elements through MCP technology without manual calibration
- **Resume Export**：Support resuming export process after interruption to avoid duplicate work
- **Structured Storage**：Store exported content in a structured way for easy subsequent management and search

## Quick Start

### Environment Requirements

- macOS system
- Python 3.9+
- Claude Code account
- WeChat for Mac

### Install Dependencies

1. Install Python dependencies：

```bash
pip install pyautogui pillow
```

2. Install MCP Server：

```bash
claude mcp add macos-control -- npx -y macos-control-mcp
```

3. Fix MCP dependencies (if encountering Quartz module error)：

```bash
unset http_proxy https_proxy
~/.macos-control-mcp/.venv/bin/pip install pyobjc-framework-Quartz pyobjc-framework-Vision
```

### Usage

1. Open WeChat and enter the Favorites page

2. Run the export script：

```bash
python3 auto_export.py [export count]
```

For example, export 100 favorites：

```bash
python3 auto_export.py 100
```

3. After export is complete, content will be saved in the `output/全部收藏/` directory, each favorite includes：
   - `screenshot.png` - Detail screenshot (auto-spliced for long content)
   - `content.txt` - Text content (if copyable)
   - `meta.json` - Metadata (time, URL, pages, etc.)

## Technical Principle

1. **UI Automation**：Use pyautogui to simulate mouse and keyboard operations
2. **MCP Integration**：Implement screen capture and OCR recognition through macos-control-mcp
3. **Retina Display Adaptation**：Solve the mapping problem between physical pixels and logical pixels
4. **Scroll Calibration**：Verify scroll effect through screenshot comparison to ensure each content is correctly exported
5. **Error Handling**：Adopt different processing strategies for different types of favorites (such as chat records)

## Notes

- **WeChat Security**：Using UI automation may have certain account banning risks, it is recommended to reasonably control operation frequency
- **Permission Requirements**：Need to grant screen recording and accessibility permissions
- **Network Environment**：Stable network connection is required when installing MCP dependencies
- **WeChat Version**：Different versions of WeChat UI may have differences, and script parameters may need to be adjusted

## Project Structure

```
NotesAssistant/
├── docs/                 # Documentation directory
│   ├── 用Claude自动导出微信收藏.md  # Detailed project description
│   └── superpowers/      # Advanced feature documentation
├── output/               # Export result directory
│   └── 全部收藏/         # WeChat Favorites export content
├── auto_export.py        # Main export script
└── README.md             # Project description
```

## Future Plans

1. **AI Summary**：Use LLM to generate summaries for each favorite
2. **Auto Classification**：Automatically categorize and tag based on content semantics
3. **Knowledge Base Integration**：Import to knowledge base tools like Obsidian
4. **Extended Support**：Support content export from other applications (such as Youdao Cloud Notes, Mubu, etc.)

## Contribution Guide

Welcome to submit Issues and Pull Requests to help improve this project.

## License

This project is licensed under the MIT License.

---

# NotesAssistant-中文

## 项目简介

NotesAssistant 是一个基于 AI 的个人知识库管理工具，专注于解决微信收藏夹等封闭系统的内容导出和管理问题。通过结合 Claude Code 和 MCP (Model Context Protocol) 技术，实现了对桌面应用的智能操控，为用户提供了一种高效、安全的知识管理解决方案。

## 主要功能

- **微信收藏夹导出**：自动批量导出微信收藏夹内容，包括截图、文本和元数据
- **长内容处理**：支持滚动拼接长截图，确保完整捕获长文章
- **智能识别**：通过 MCP 技术自动识别 UI 元素，无需手动校准
- **断点续传**：支持导出过程中断后继续执行，避免重复工作
- **结构化存储**：将导出内容以结构化方式存储，方便后续管理和搜索

## 快速开始

### 环境要求

- macOS 系统
- Python 3.9+
- Claude Code 账号
- 微信 Mac 版

### 安装依赖

1. 安装 Python 依赖：

```bash
pip install pyautogui pillow
```

2. 安装 MCP Server：

```bash
claude mcp add macos-control -- npx -y macos-control-mcp
```

3. 修复 MCP 依赖（如果遇到 Quartz 模块错误）：

```bash
unset http_proxy https_proxy
~/.macos-control-mcp/.venv/bin/pip install pyobjc-framework-Quartz pyobjc-framework-Vision
```

### 使用方法

1. 打开微信并进入收藏夹页面

2. 运行导出脚本：

```bash
python3 auto_export.py [导出数量]
```

例如，导出100条收藏：

```bash
python3 auto_export.py 100
```

3. 导出完成后，内容会保存在 `output/全部收藏/` 目录中，每条收藏包含：
   - `screenshot.png` - 详情截图（长内容自动拼接）
   - `content.txt` - 文本内容（如可复制）
   - `meta.json` - 元数据（时间、URL、页数等）

## 技术原理

1. **UI 自动化**：使用 pyautogui 模拟鼠标和键盘操作
2. **MCP 集成**：通过 macos-control-mcp 实现屏幕截图和 OCR 识别
3. **Retina 显示屏适配**：解决物理像素和逻辑像素的映射问题
4. **滚动校准**：通过截图对比验证滚动效果，确保每条内容都被正确导出
5. **错误处理**：针对不同类型的收藏（如聊天记录）采用不同的处理策略

## 注意事项

- **微信安全**：使用 UI 自动化可能存在一定的封号风险，建议合理控制操作频率
- **权限要求**：需要授予屏幕录制和辅助功能权限
- **网络环境**：安装 MCP 依赖时需要稳定的网络连接
- **微信版本**：不同版本的微信 UI 可能存在差异，可能需要调整脚本参数

## 项目结构

```
NotesAssistant/
├── docs/                 # 文档目录
│   ├── 用Claude自动导出微信收藏.md  # 项目详细说明
│   └── superpowers/      # 高级功能文档
├── output/               # 导出结果目录
│   └── 全部收藏/         # 微信收藏导出内容
├── auto_export.py        # 主要导出脚本
└── README.md             # 项目说明
```

## 下一步计划

1. **AI 摘要**：使用 LLM 对每条收藏生成摘要
2. **自动分类**：根据内容语义自动归类和打标签
3. **知识库集成**：导入 Obsidian 等知识库工具
4. **扩展支持**：支持其他应用（如有道云笔记、幕布等）的内容导出

## 贡献指南

欢迎提交 Issue 和 Pull Request，帮助改进这个项目。

## 许可证

本项目采用 MIT 许可证。