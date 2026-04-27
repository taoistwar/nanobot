Update memory files based on the analysis below.
根据下面的分析更新记忆文件。
- [FILE] entries: add the described content to the appropriate file
- [FILE] 条目：将描述的内容添加到适当文件
- [FILE-REMOVE] entries: delete the corresponding content from memory files
- [FILE-REMOVE] 条目：从记忆文件中删除对应内容
- [SKILL] entries: create a new skill under skills/<name>/SKILL.md using write_file
- [SKILL] 条目：使用 write_file 在 skills/<name>/SKILL.md 下创建新 skill

## File paths (relative to workspace root)
## 文件路径（相对于工作区根目录）
- SOUL.md
- USER.md
- memory/MEMORY.md
- skills/<name>/SKILL.md (for [SKILL] entries only)
- skills/<name>/SKILL.md（仅用于 [SKILL] 条目）

Do NOT guess paths.
不要猜测路径。

## Editing rules
## 编辑规则
- Edit directly — file contents provided below, no read_file needed
- 直接编辑，文件内容已在下方提供，无需 read_file
- Use exact text as old_text, include surrounding blank lines for unique match
- 使用精确文本作为 old_text，并包含周围空行以确保唯一匹配
- Batch changes to the same file into one edit_file call
- 将同一文件的变更合并到一次 edit_file 调用中
- For deletions: section header + all bullets as old_text, new_text empty
- 对删除操作：将章节标题和所有项目符号作为 old_text，new_text 为空
- Surgical edits only — never rewrite entire files
- 只进行外科手术式编辑，绝不要重写整个文件
- If nothing to update, stop without calling tools
- 如果没有要更新的内容，不调用工具并停止

## Skill creation rules (for [SKILL] entries)
## Skill 创建规则（用于 [SKILL] 条目）
- Use write_file to create skills/<name>/SKILL.md
- 使用 write_file 创建 skills/<name>/SKILL.md
- Before writing, read_file `{{ skill_creator_path }}` for format reference (frontmatter structure, naming conventions, quality standards)
- 写入前，read_file `{{ skill_creator_path }}` 作为格式参考（frontmatter 结构、命名约定、质量标准）
- **Dedup check**: read existing skills listed below to verify the new skill is not functionally redundant. Skip creation if an existing skill already covers the same workflow.
- **去重检查**：读取下方列出的现有 skills，确认新 skill 在功能上不冗余。如果已有 skill 覆盖同一工作流，则跳过创建。
- Include YAML frontmatter with name and description fields
- 包含带有 name 和 description 字段的 YAML frontmatter
- Keep SKILL.md under 2000 words — concise and actionable
- 将 SKILL.md 控制在 2000 词以内，保持简洁且可执行
- Include: when to use, steps, output format, at least one example
- 包含：何时使用、步骤、输出格式、至少一个示例
- Do NOT overwrite existing skills — skip if the skill directory already exists
- 不要覆盖现有 skills，如果 skill 目录已存在则跳过
- Reference specific tools the agent has access to (read_file, write_file, exec, web_search, etc.)
- 引用 agent 可访问的具体工具（read_file、write_file、exec、web_search 等）
- Skills are instruction sets, not code — do not include implementation code
- Skills 是指令集，不是代码，不要包含实现代码

## Quality
## 质量
- Every line must carry standalone value
- 每一行都必须具有独立价值
- Concise bullets under clear headers
- 在清晰标题下使用简洁项目符号
- When reducing (not deleting): keep essential facts, drop verbose details
- 缩减（而非删除）时：保留关键事实，去掉冗长细节
- If uncertain whether to delete, keep but add "(verify currency)"
- 如果不确定是否删除，则保留但添加 "(verify currency)"
