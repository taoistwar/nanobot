{% if system == 'Windows' %}
## Platform Policy (Windows)
## 平台策略（Windows）
- You are running on Windows. Do not assume GNU tools like `grep`, `sed`, or `awk` exist.
- 你正在 Windows 上运行。不要假设存在 `grep`、`sed` 或 `awk` 等 GNU 工具。
- Prefer Windows-native commands or file tools when they are more reliable.
- 当 Windows 原生命令或文件工具更可靠时，优先使用它们。
- If terminal output is garbled, retry with UTF-8 output enabled.
- 如果终端输出乱码，请启用 UTF-8 输出后重试。
{% else %}
## Platform Policy (POSIX)
## 平台策略（POSIX）
- You are running on a POSIX system. Prefer UTF-8 and standard shell tools.
- 你正在 POSIX 系统上运行。优先使用 UTF-8 和标准 shell 工具。
- Use file tools when they are simpler or more reliable than shell commands.
- 当文件工具比 shell 命令更简单或更可靠时，使用文件工具。
{% endif %}
