# Tick

> 终端美学待办管理 · Vim-style TUI Task Manager

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Textual](https://img.shields.io/badge/Textual-8.2-teal.svg)](https://github.com/Textualize/textual)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**简洁高效 · 类 Vim 交互 · 多视图管理**

</div>

---

## Features

- **美观 TUI 界面** — 边框布局、状态栏、清晰的任务列表
- **类 Vim 交互** — `j/k` 导航，快捷键操作，零学习成本
- **多视图切换** — 清单视图、日历视图、分类视图
- **时间维度管理** — 支持截止日期、优先级、分类
- **主题自定义** — 按 `Ctrl+P` 切换主题，设置自动保存
- **轻量无负担** — 启动快，无复杂依赖

## Install

```bash
pip install tick
```

或直接运行：

```bash
python -m tick
```

## Usage

| Key | Action |
|-----|--------|
| `n` | 新建任务 |
| `e` | 编辑任务 |
| `d` | 删除任务 |
| `Enter` | 切换完成状态 |
| `1/2/3` | 切换视图（清单/日历/分类） |
| `Ctrl+P` | 命令面板（切换主题） |
| `q` | 退出 |

## Preview

启动后直接进入主界面：

```
┌──────────────────────────────────────────────┐
│  Tick  [清单视图]                             │
├──────────────────────────────────────────────┤
│  [ ] 完成项目文档 | 截止:2026-04-25 | 高优先级 │
│  [x] 代码审查     | 截止:2026-04-20 | 已完成  │
│                                              │
├──────────────────────────────────────────────┤
│  总数:5 | 已完成:2 | 1/2/3切换 n新建 q退出   │
└──────────────────────────────────────────────┘
```

## Philosophy

> 让终端不再只是执行命令，也能成为优雅的生产力空间。

## License

MIT
