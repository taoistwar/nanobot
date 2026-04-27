---
name: my
description: Check and set the agent's own runtime state (model, iterations, context window, token usage, web config). Use when diagnosing why something doesn't work ("why can't you search the web?", "why did you stop?"), checking resource limits before complex tasks, adapting configuration for long or simple tasks, or remembering user preferences across turns. Also use when the user asks what model you are running, how many tokens you've used, or what your settings are.
always: true
---

# Self-Awareness
自我感知

## How to use
如何使用

1. **Identify the situation** from the categories below
1. **Identify the situation** 从下面的类别中识别场景
2. **Call the my tool** with the appropriate action
2. **Call the my tool** 使用合适的 action 调用 my 工具
3. **If set**, warn the user before changing impactful settings (model, iterations)
3. **If set**，在更改有影响的设置（model、iterations）前提醒用户
4. **For detailed examples**, read [references/examples.md](references/examples.md)
4. **For detailed examples**，阅读 [references/examples.md](references/examples.md)

## When to check
何时检查

<rule>
**Diagnose before explaining.** When something doesn't work, check your state first.
**先诊断再解释。**当某些内容无法工作时，先检查自身状态。
</rule>

<rule>
**Check budget before complex tasks.** Know your limits before committing.
**复杂任务前先检查预算。**承诺任务前先了解自身限制。
</rule>

<rule>
**Recall across turns.** Store preferences in your scratchpad, read them back later.
**跨轮次回忆。**将偏好存储在 scratchpad 中，稍后再读回。
</rule>

## When to set
何时设置

<rule>
**Only set when benefit is clear and user is informed.** Warn before changing model.
**只有收益明确且用户知情时才设置。**更改模型前先提醒。
</rule>

| Situation | Command |
|-----------|---------|
| Large codebase analysis | `my(action="set", key="context_window_tokens", value=131072)` |
| 大型代码库分析 | `my(action="set", key="context_window_tokens", value=131072)` |
| Repetitive simple tasks | `my(action="set", key="model", value="<fast-model>")` |
| 重复的简单任务 | `my(action="set", key="model", value="<fast-model>")` |
| Long multi-step task | `my(action="set", key="max_iterations", value=80)` |
| 较长的多步骤任务 | `my(action="set", key="max_iterations", value=80)` |

**Tradeoff:** Bias toward stability. Only set when defaults are genuinely insufficient.
**权衡：**偏向稳定性。只有默认值确实不足时才设置。

## Anti-patterns
反模式

<rule>
**Don't check every turn.** Costs a tool call. Use when you need information, not reflexively.
**不要每轮都检查。**这会消耗一次工具调用。需要信息时再使用，不要条件反射式调用。
</rule>

<rule>
**Don't store sensitive data.** No API keys, passwords, or tokens in scratchpad.
**不要存储敏感数据。**不要在 scratchpad 中保存 API key、密码或 token。
</rule>

<rule>
**Don't set workspace.** Does not update file tool boundaries — won't work.
**不要设置 workspace。**这不会更新文件工具边界，因此不会生效。
</rule>

## Constraints
约束

- All modifications in-memory only — restart resets everything
- 所有修改仅在内存中；重启会重置一切
- Protected params have type/range validation: `max_iterations` (1–100), `context_window_tokens` (4096–1M), `model` (non-empty str)
- 受保护参数具有类型/范围校验：`max_iterations`（1–100）、`context_window_tokens`（4096–1M）、`model`（非空字符串）
- If `tools.my.allow_set` is false, check only
- 如果 `tools.my.allow_set` 为 false，则只能检查

## Related tools
相关工具

| Need | Use | Persists? |
|------|-----|-----------|
| Per-session temp state | `my(action="set", key="...", value=...)` | No |
| 每会话临时状态 | `my(action="set", key="...", value=...)` | 否 |
| Long-term facts | Memory skill (`MEMORY.md`, `USER.md`) | Yes |
| 长期事实 | Memory 技能（`MEMORY.md`、`USER.md`） | 是 |
| Permanent config change | Edit config file | Yes |
| 永久配置变更 | 编辑配置文件 | 是 |

**Rule of thumb:** Tomorrow? Memory. This turn only? My.
**经验法则：**明天还需要？用 Memory。只在本轮需要？用 My。
