---
name: tmux
description: Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output.
metadata: {"nanobot":{"emoji":"🧵","os":["darwin","linux"],"requires":{"bins":["tmux"]}}}
---

# tmux Skill
tmux 技能

Use tmux only when you need an interactive TTY. Prefer exec background mode for long-running, non-interactive tasks.
仅在需要交互式 TTY 时使用 tmux。对于长时间运行的非交互任务，优先使用 exec 后台模式。

## Quickstart (isolated socket, exec tool)
快速开始（隔离 socket，exec 工具）

```bash
SOCKET_DIR="${NANOBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/nanobot-tmux-sockets}"
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/nanobot.sock"
SESSION=nanobot-python

tmux -S "$SOCKET" new -d -s "$SESSION" -n shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'PYTHON_BASIC_REPL=1 python3 -q' Enter
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200
```

After starting a session, always print monitor commands:
启动会话后，始终打印监控命令：

```
To monitor:
  tmux -S "$SOCKET" attach -t "$SESSION"
  tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200
```

## Socket convention
Socket 约定

- Use `NANOBOT_TMUX_SOCKET_DIR` environment variable.
- 使用 `NANOBOT_TMUX_SOCKET_DIR` 环境变量。
- Default socket path: `"$NANOBOT_TMUX_SOCKET_DIR/nanobot.sock"`.
- 默认 socket 路径：`"$NANOBOT_TMUX_SOCKET_DIR/nanobot.sock"`。

## Targeting panes and naming
定位 pane 与命名

- Target format: `session:window.pane` (defaults to `:0.0`).
- 目标格式：`session:window.pane`（默认值为 `:0.0`）。
- Keep names short; avoid spaces.
- 名称保持简短；避免空格。
- Inspect: `tmux -S "$SOCKET" list-sessions`, `tmux -S "$SOCKET" list-panes -a`.
- 检查：`tmux -S "$SOCKET" list-sessions`、`tmux -S "$SOCKET" list-panes -a`。

## Finding sessions
查找会话

- List sessions on your socket: `{baseDir}/scripts/find-sessions.sh -S "$SOCKET"`.
- 列出你的 socket 上的会话：`{baseDir}/scripts/find-sessions.sh -S "$SOCKET"`。
- Scan all sockets: `{baseDir}/scripts/find-sessions.sh --all` (uses `NANOBOT_TMUX_SOCKET_DIR`).
- 扫描所有 socket：`{baseDir}/scripts/find-sessions.sh --all`（使用 `NANOBOT_TMUX_SOCKET_DIR`）。

## Sending input safely
安全发送输入

- Prefer literal sends: `tmux -S "$SOCKET" send-keys -t target -l -- "$cmd"`.
- 优先按字面量发送：`tmux -S "$SOCKET" send-keys -t target -l -- "$cmd"`。
- Control keys: `tmux -S "$SOCKET" send-keys -t target C-c`.
- 控制键：`tmux -S "$SOCKET" send-keys -t target C-c`。

## Watching output
观察输出

- Capture recent history: `tmux -S "$SOCKET" capture-pane -p -J -t target -S -200`.
- 捕获最近历史：`tmux -S "$SOCKET" capture-pane -p -J -t target -S -200`。
- Wait for prompts: `{baseDir}/scripts/wait-for-text.sh -t session:0.0 -p 'pattern'`.
- 等待提示符：`{baseDir}/scripts/wait-for-text.sh -t session:0.0 -p 'pattern'`。
- Attaching is OK; detach with `Ctrl+b d`.
- 可以 attach；使用 `Ctrl+b d` detach。

## Spawning processes
生成进程

- For python REPLs, set `PYTHON_BASIC_REPL=1` (non-basic REPL breaks send-keys flows).
- 对于 Python REPL，设置 `PYTHON_BASIC_REPL=1`（非 basic REPL 会破坏 send-keys 流程）。

## Windows / WSL
Windows / WSL

- tmux is supported on macOS/Linux. On Windows, use WSL and install tmux inside WSL.
- tmux 支持 macOS/Linux。在 Windows 上，使用 WSL 并在 WSL 内安装 tmux。
- This skill is gated to `darwin`/`linux` and requires `tmux` on PATH.
- 此技能仅限 `darwin`/`linux`，并要求 PATH 中存在 `tmux`。

## Orchestrating Coding Agents (Codex, Claude Code)
编排编码 Agent（Codex、Claude Code）

tmux excels at running multiple coding agents in parallel:
tmux 擅长并行运行多个编码 agent：

```bash
SOCKET="${TMPDIR:-/tmp}/codex-army.sock"

# Create multiple sessions
for i in 1 2 3 4 5; do
  tmux -S "$SOCKET" new-session -d -s "agent-$i"
done

# Launch agents in different workdirs
tmux -S "$SOCKET" send-keys -t agent-1 "cd /tmp/project1 && codex --yolo 'Fix bug X'" Enter
tmux -S "$SOCKET" send-keys -t agent-2 "cd /tmp/project2 && codex --yolo 'Fix bug Y'" Enter

# Poll for completion (check if prompt returned)
for sess in agent-1 agent-2; do
  if tmux -S "$SOCKET" capture-pane -p -t "$sess" -S -3 | grep -q "❯"; then
    echo "$sess: DONE"
  else
    echo "$sess: Running..."
  fi
done

# Get full output from completed session
tmux -S "$SOCKET" capture-pane -p -t agent-1 -S -500
```

**Tips:**
**提示：**
- Use separate git worktrees for parallel fixes (no branch conflicts)
- 为并行修复使用独立的 git worktree（避免分支冲突）
- `pnpm install` first before running codex in fresh clones
- 在全新 clone 中运行 codex 前，先执行 `pnpm install`
- Check for shell prompt (`❯` or `$`) to detect completion
- 检查 shell 提示符（`❯` 或 `$`）以检测完成状态
- Codex needs `--yolo` or `--full-auto` for non-interactive fixes
- Codex 需要 `--yolo` 或 `--full-auto` 来执行非交互式修复

## Cleanup
清理

- Kill a session: `tmux -S "$SOCKET" kill-session -t "$SESSION"`.
- 终止一个会话：`tmux -S "$SOCKET" kill-session -t "$SESSION"`。
- Kill all sessions on a socket: `tmux -S "$SOCKET" list-sessions -F '#{session_name}' | xargs -r -n1 tmux -S "$SOCKET" kill-session -t`.
- 终止某个 socket 上的所有会话：`tmux -S "$SOCKET" list-sessions -F '#{session_name}' | xargs -r -n1 tmux -S "$SOCKET" kill-session -t`。
- Remove everything on the private socket: `tmux -S "$SOCKET" kill-server`.
- 移除私有 socket 上的所有内容：`tmux -S "$SOCKET" kill-server`。

## Helper: wait-for-text.sh
辅助工具：wait-for-text.sh

`{baseDir}/scripts/wait-for-text.sh` polls a pane for a regex (or fixed string) with a timeout.
`{baseDir}/scripts/wait-for-text.sh` 会在超时时间内轮询 pane，查找正则表达式（或固定字符串）。

```bash
{baseDir}/scripts/wait-for-text.sh -t session:0.0 -p 'pattern' [-F] [-T 20] [-i 0.5] [-l 2000]
```

- `-t`/`--target` pane target (required)
- `-t`/`--target` pane 目标（必需）
- `-p`/`--pattern` regex to match (required); add `-F` for fixed string
- `-p`/`--pattern` 要匹配的正则表达式（必需）；添加 `-F` 表示固定字符串
- `-T` timeout seconds (integer, default 15)
- `-T` 超时秒数（整数，默认 15）
- `-i` poll interval seconds (default 0.5)
- `-i` 轮询间隔秒数（默认 0.5）
- `-l` history lines to search (integer, default 1000)
- `-l` 要搜索的历史行数（整数，默认 1000）
