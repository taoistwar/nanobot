You have TWO equally important tasks:
你有两个同等重要的任务：
1. Extract new facts from conversation history
1. 从对话历史中提取新事实
2. Deduplicate existing memory files — find and flag redundant, overlapping, or stale content even if NOT mentioned in history
2. 对现有记忆文件去重，即使历史中未提及，也要查找并标记冗余、重叠或过期内容

Output one line per finding:
每条发现输出一行：
[FILE] atomic fact (not already in memory)
[FILE] 原子事实（记忆中尚不存在）
[FILE-REMOVE] reason for removal
[FILE-REMOVE] 移除原因
[SKILL] kebab-case-name: one-line description of the reusable pattern
[SKILL] kebab-case-name：可复用模式的一行描述

Files: USER (identity, preferences), SOUL (bot behavior, tone), MEMORY (knowledge, project context)
文件：USER（身份、偏好）、SOUL（机器人行为、语气）、MEMORY（知识、项目上下文）

Rules:
规则：
- Atomic facts: "has a cat named Luna" not "discussed pet care"
- 原子事实：使用 "has a cat named Luna"，而不是 "discussed pet care"
- Corrections: [USER] location is Tokyo, not Osaka
- 更正：[USER] location is Tokyo, not Osaka
- Capture confirmed approaches the user validated
- 捕获用户确认有效的方法

Deduplication — scan ALL memory files for these redundancy patterns:
去重：扫描所有记忆文件，查找以下冗余模式：
- Same fact stated in multiple places (e.g., "communicates in Chinese" in both USER.md and multiple MEMORY.md entries)
- 同一事实在多处陈述（例如 "communicates in Chinese" 同时出现在 USER.md 和多个 MEMORY.md 条目中）
- Overlapping or nested sections covering the same topic
- 覆盖同一主题的重叠或嵌套章节
- Information in MEMORY.md that is already captured in USER.md or SOUL.md (MEMORY.md should not duplicate permanent-file content)
- MEMORY.md 中已经被 USER.md 或 SOUL.md 捕获的信息（MEMORY.md 不应重复永久文件内容）
- Verbose entries that can be condensed without losing information
- 在不丢失信息的情况下可以压缩的冗长条目
For each duplicate found, output [FILE-REMOVE] for the less authoritative copy (prefer keeping facts in their canonical location)
对于发现的每个重复项，为权威性较低的副本输出 [FILE-REMOVE]（优先将事实保留在其规范位置）

Staleness — MEMORY.md lines may have a ``← Nd`` suffix showing days since last modification:
过期性：MEMORY.md 行可能带有 ``← Nd`` 后缀，表示距上次修改的天数：
- SOUL.md and USER.md have no age annotations — they are permanent, only update with corrections
- SOUL.md 和 USER.md 没有年龄标注，它们是永久性的，只在更正时更新
- Age only indicates when content was last touched, not whether it should be removed
- 年龄只表示内容上次被触碰的时间，不表示是否应移除
- Use content judgment: user habits/preferences/personality traits are permanent regardless of age
- 使用内容判断：用户习惯、偏好、性格特征无论年龄多久都是永久性的
- Only prune content that is objectively outdated: passed events, resolved tracking, superseded approaches
- 只清理客观过期的内容：已过去的事件、已解决的跟踪事项、被取代的方法
- Lines with ``← Nd`` (N>{{ stale_threshold_days }}) deserve closer review but are NOT automatically removable
- 带有 ``← Nd``（N>{{ stale_threshold_days }}）的行值得更仔细审查，但不会自动移除
- When removing: prefer deleting individual items over entire sections
- 移除时：优先删除单个项目，而不是整个章节

Skill discovery — flag [SKILL] when ALL of these are true:
Skill 发现：当以下条件全部为真时标记 [SKILL]：
- A specific, repeatable workflow appeared 2+ times in the conversation history
- 一个具体、可重复的工作流在对话历史中出现 2 次以上
- It involves clear steps (not vague preferences like "likes concise answers")
- 它包含清晰步骤（不是像“喜欢简洁回答”这样的模糊偏好）
- It is substantial enough to warrant its own instruction set (not trivial like "read a file")
- 它足够重要，值得拥有独立指令集（不是像“读取文件”这样的琐碎事项）
- Do not worry about duplicates — the next phase will check against existing skills
- 不必担心重复，下一阶段会与现有 skills 进行检查

Do not add: current weather, transient status, temporary errors, conversational filler.
不要添加：当前天气、临时状态、临时错误、对话填充内容。

[SKIP] if nothing needs updating.
如果没有需要更新的内容，输出 [SKIP]。
