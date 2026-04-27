# Agent Instructions
# Agent 指令

## Scheduled Reminders
## 定时提醒

Before scheduling reminders, check available skills and follow skill guidance first.
在安排提醒之前，请先检查可用 skills 并遵循 skill 指引。
Use the built-in `cron` tool to create/list/remove jobs (do not call `nanobot cron` via `exec`).
使用内置 `cron` 工具创建、列出或移除任务（不要通过 `exec` 调用 `nanobot cron`）。
Get USER_ID and CHANNEL from the current session (e.g., `8281248569` and `telegram` from `telegram:8281248569`).
从当前会话获取 USER_ID 和 CHANNEL（例如从 `telegram:8281248569` 获取 `8281248569` 和 `telegram`）。

**Do NOT just write reminders to MEMORY.md** — that won't trigger actual notifications.
**不要只是把提醒写入 MEMORY.md**，那不会触发实际通知。

## Heartbeat Tasks
## 心跳任务

`HEARTBEAT.md` is checked on the configured heartbeat interval. Use file tools to manage periodic tasks:
`HEARTBEAT.md` 会按配置的心跳间隔被检查。使用文件工具管理周期性任务：

- **Add**: `edit_file` to append new tasks
- **添加**：使用 `edit_file` 追加新任务
- **Remove**: `edit_file` to delete completed tasks
- **移除**：使用 `edit_file` 删除已完成任务
- **Rewrite**: `write_file` to replace all tasks
- **重写**：使用 `write_file` 替换所有任务

When the user asks for a recurring/periodic task, update `HEARTBEAT.md` instead of creating a one-time cron reminder.
当用户请求重复性或周期性任务时，更新 `HEARTBEAT.md`，而不是创建一次性 cron 提醒。
