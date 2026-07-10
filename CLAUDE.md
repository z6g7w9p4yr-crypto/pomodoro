# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

桌面番茄钟，Python + CustomTkinter 图形界面。单文件应用，专注 25 分钟 / 休息 5 分钟自动切换，圆环倒计时 + 提示音。

## Run

```powershell
pythonw "C:\Users\13910\番茄钟\pomodoro.py"
```

桌面有快捷方式 `番茄钟.lnk`，双击也可启动。

## Dependencies

| 依赖 | 安装 |
|------|------|
| Python 3.13 | 已装，`C:\Users\13910\AppData\Local\Programs\Python\Python313\` |
| customtkinter | `python -m pip install customtkinter`（已装） |
| winsound | Python 自带，无需安装 |

无其他第三方依赖。

## Architecture

单文件 `pomodoro.py`，一个类 `PomodoroApp`：

- **状态字段**：`is_focus`（专注/休息）、`remaining`（剩余秒数）、`running`（是否计时中）
- **`total` 是 `@property`**，由 `is_focus` + `focus_minutes`/`break_minutes` 自动派生，不单独存
- **计时**：`root.after(1000, self._tick)` 每秒递减，纯事件驱动，无 busy-loop
- **阶段切换**：统一走 `_advance_phase()`，`_phase_finished` 和 `skip` 都通过它切换
- **圆环**：tkinter Canvas `create_arc`，根据 `remaining/total` 比例画弧
- **提示音**：后台线程 `winsound.Beep`，不阻塞界面
- **颜色**：专注珊瑚红 `FOCUS_COLOR` / 休息青绿 `BREAK_COLOR`，深色主题

## Git

已配置 SSH 密钥，推送到 GitHub：
- 仓库：`git@github.com:z6g7w9p4yr-crypto/pomodoro.git`
- 分支：`main`
- 用户名：`z6g7w9p4yr-crypto`
- 邮箱：`gudapang2007@163.com`

## API 后端

Claude Code 通过 DeepSeek 兼容 API 运行，配置在 `C:\Users\13910\.claude\settings.json`：
- 端点：`https://api.deepseek.com/anthropic`
- 模型：`deepseek-v4-pro`（所有模型类型统一映射到此）

## Notes

- 用户是编程初学者，今天是学习第一天，解释技术概念时应保持简洁易懂
- 用户使用 Windows 11 + PowerShell 5.1，注意 PowerShell 语法兼容性（无 `&&`、无三元运算符、无 `2>&1` 等）
- 安装软件优先用 `winget`，其次用 `pip`
