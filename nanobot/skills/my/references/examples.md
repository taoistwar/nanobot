# My Tool — Practical Examples
My 工具 — 实用示例

Concrete scenarios showing when and how to use the my tool effectively.
展示何时以及如何有效使用 my 工具的具体场景。

## Diagnosis
诊断

### "Why can't you search the web?"
“你为什么不能搜索网页？”
```
→ my(action="check", key="web_config.enable")
  → False
→ "Web search is disabled. Add web.enable: true to your config to enable it."
```

### "Why did you stop?"
“你为什么停下了？”
```
→ my(action="check", key="max_iterations")
  → 40
→ my(action="check", key="_last_usage")
  → {"prompt_tokens": 62000, "completion_tokens": 3000}
→ "I hit the iteration limit (40). The task was complex. I can ask the user if they want to increase it."
```

### "What model are you running?"
“你正在运行什么模型？”
```
→ my(action="check", key="model")
  → 'anthropic/claude-sonnet-4-20250514'
```

## Adaptive Behavior
自适应行为

### Large codebase analysis
大型代码库分析
```
→ my(action="check")
  → context_window_tokens: 65536
→ my(action="set", key="context_window_tokens", value=131072)
  → "Set context_window_tokens = 131072 (was 65536)"
→ "I've expanded my context window to handle this large codebase."
```

### Switching to a faster model for repetitive tasks
为重复性任务切换到更快的模型
```
→ my(action="set", key="model", value="anthropic/claude-haiku-4-5-20251001")
  → "Set model = 'anthropic/claude-haiku-4-5-20251001' (was 'anthropic/claude-sonnet-4-20250514')"
→ "Switched to a faster model for these batch tasks."
```

## Cross-Turn Memory
跨轮次记忆

### Remembering user preferences
记住用户偏好
```
# Turn 1: user says "keep it brief"
→ my(action="set", key="user_style", value="concise")
  → "Set scratchpad.user_style = 'concise'"

# Turn 3: new topic
→ my(action="check", key="user_style")
  → 'concise'
  (adjusts response style accordingly)
```

### Tracking project context
跟踪项目上下文
```
→ my(action="set", key="active_branch", value="feat/auth")
→ my(action="set", key="test_framework", value="pytest")
→ my(action="set", key="has_docker", value=true)
```

## Budget Awareness
预算感知

### Token-conscious behavior
Token 感知行为
```
→ my(action="check", key="_last_usage")
  → {"prompt_tokens": 58000, "completion_tokens": 12000}
→ "I've consumed ~70k tokens. I'll keep my remaining responses focused."
```
