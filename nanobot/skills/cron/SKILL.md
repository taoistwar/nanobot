---
name: cron
description: Schedule reminders and recurring tasks.
---

# Cron
Cron

Use the `cron` tool to schedule reminders or recurring tasks.
使用 `cron` 工具安排提醒或重复任务。

## Three Modes
三种模式

1. **Reminder** - message is sent directly to user
1. **Reminder** - 消息会直接发送给用户
2. **Task** - message is a task description, agent executes and sends result
2. **Task** - 消息是任务描述，agent 执行后发送结果
3. **One-time** - runs once at a specific time, then auto-deletes
3. **One-time** - 在特定时间运行一次，然后自动删除

## Examples
示例

Fixed reminder:
固定提醒：
```
cron(action="add", message="Time to take a break!", every_seconds=1200)
```

Dynamic task (agent executes each time):
动态任务（agent 每次都会执行）：
```
cron(action="add", message="Check HKUDS/nanobot GitHub stars and report", every_seconds=600)
```

One-time scheduled task (compute ISO datetime from current time):
一次性计划任务（根据当前时间计算 ISO datetime）：
```
cron(action="add", message="Remind me about the meeting", at="<ISO datetime>")
```

Timezone-aware cron:
感知时区的 cron：
```
cron(action="add", message="Morning standup", cron_expr="0 9 * * 1-5", tz="America/Vancouver")
```

List/remove:
列出或移除：
```
cron(action="list")
cron(action="remove", job_id="abc123")
```

## Time Expressions
时间表达式

| User says | Parameters |
|-----------|------------|
| every 20 minutes | every_seconds: 1200 |
| 每 20 分钟 | every_seconds: 1200 |
| every hour | every_seconds: 3600 |
| 每小时 | every_seconds: 3600 |
| every day at 8am | cron_expr: "0 8 * * *" |
| 每天早上 8 点 | cron_expr: "0 8 * * *" |
| weekdays at 5pm | cron_expr: "0 17 * * 1-5" |
| 工作日下午 5 点 | cron_expr: "0 17 * * 1-5" |
| 9am Vancouver time daily | cron_expr: "0 9 * * *", tz: "America/Vancouver" |
| 每天温哥华时间上午 9 点 | cron_expr: "0 9 * * *", tz: "America/Vancouver" |
| at a specific time | at: ISO datetime string (compute from current time) |
| 在特定时间 | at: ISO datetime 字符串（根据当前时间计算） |

## Timezone
时区

Use `tz` with `cron_expr` to schedule in a specific IANA timezone. Without `tz`, the server's local timezone is used.
将 `tz` 与 `cron_expr` 搭配使用，可在特定 IANA 时区中安排任务。不使用 `tz` 时，会使用服务器的本地时区。
