---
name: skill-creator
description: Create or update AgentSkills. Use when designing, structuring, or packaging skills with scripts, references, and assets.
---

# Skill Creator
技能创建器

This skill provides guidance for creating effective skills.
此技能为创建有效技能提供指导。

## About Skills
关于技能

Skills are modular, self-contained packages that extend the agent's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks—they transform the agent from a general-purpose agent into a specialized agent
equipped with procedural knowledge that no model can fully possess.
技能是模块化、自包含的包，通过提供专门知识、工作流和工具来扩展 agent 的能力。可以把它们看作特定领域或任务的“入职指南”；它们将 agent 从通用 agent 转变为具备程序性知识的专门 agent，而这些知识不是任何模型都能完全具备的。

### What Skills Provide
技能提供什么

1. Specialized workflows - Multi-step procedures for specific domains
1. Specialized workflows - 面向特定领域的多步骤流程
2. Tool integrations - Instructions for working with specific file formats or APIs
2. Tool integrations - 使用特定文件格式或 API 的说明
3. Domain expertise - Company-specific knowledge, schemas, business logic
3. Domain expertise - 公司特定知识、schema、业务逻辑
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks
4. Bundled resources - 用于复杂和重复任务的脚本、参考资料和资产

## Core Principles
核心原则

### Concise is Key
简洁是关键

The context window is a public good. Skills share the context window with everything else the agent needs: system prompt, conversation history, other Skills' metadata, and the actual user request.
上下文窗口是一种公共资源。技能会与 agent 所需的其他所有内容共享上下文窗口：system prompt、对话历史、其他技能的 metadata，以及实际用户请求。

**Default assumption: the agent is already very smart.** Only add context the agent doesn't already have. Challenge each piece of information: "Does the agent really need this explanation?" and "Does this paragraph justify its token cost?"
**默认假设：agent 已经很聪明。**只添加 agent 尚不具备的上下文。审视每一条信息：“agent 真的需要这段解释吗？”以及“这段内容值得消耗这些 token 吗？”

Prefer concise examples over verbose explanations.
优先使用简洁示例，而不是冗长解释。

### Set Appropriate Degrees of Freedom
设置适当的自由度

Match the level of specificity to the task's fragility and variability:
让具体程度匹配任务的脆弱性和可变性：

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.
**高自由度（基于文本的指令）**：当多种方法都有效、决策依赖上下文，或需要启发式方法指导时使用。

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.
**中等自由度（伪代码或带参数的脚本）**：当存在首选模式、允许一定变化，或配置会影响行为时使用。

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.
**低自由度（具体脚本、少量参数）**：当操作脆弱且易出错、一致性很关键，或必须遵循特定顺序时使用。

Think of the agent as exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many routes (high freedom).
把 agent 想象成在探索路径：悬崖边的窄桥需要明确护栏（低自由度），而开阔田野允许多条路线（高自由度）。

### Anatomy of a Skill
技能的组成

Every skill consists of a required SKILL.md file and optional bundled resources:
每个技能都由一个必需的 SKILL.md 文件和可选的捆绑资源组成：

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (required)
SKILL.md（必需）

Every SKILL.md consists of:
每个 SKILL.md 都包含：

- **Frontmatter** (YAML): Contains `name` and `description` fields. These are the only fields that the agent reads to determine when the skill gets used, thus it is very important to be clear and comprehensive in describing what the skill is, and when it should be used.
- **Frontmatter**（YAML）：包含 `name` 和 `description` 字段。这些是 agent 用来判断何时使用技能的唯一字段，因此清晰、全面地描述技能是什么以及何时使用非常重要。
- **Body** (Markdown): Instructions and guidance for using the skill. Only loaded AFTER the skill triggers (if at all).
- **Body**（Markdown）：使用技能的说明和指导。仅在技能触发后才会加载（如果触发的话）。

#### Bundled Resources (optional)
捆绑资源（可选）

##### Scripts (`scripts/`)
脚本（`scripts/`）

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.
用于需要确定性可靠性或会被反复重写的任务的可执行代码（Python/Bash 等）。

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **When to include**：当相同代码被反复重写，或需要确定性可靠性时
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Example**：用于 PDF 旋转任务的 `scripts/rotate_pdf.py`
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Benefits**：节省 token、具备确定性，可在不加载到上下文的情况下执行
- **Note**: Scripts may still need to be read by the agent for patching or environment-specific adjustments
- **Note**：agent 可能仍需读取脚本，以便打补丁或进行环境特定调整

##### References (`references/`)
参考资料（`references/`）

Documentation and reference material intended to be loaded as needed into context to inform the agent's process and thinking.
按需加载到上下文中的文档和参考材料，用于辅助 agent 的流程和思考。

- **When to include**: For documentation that the agent should reference while working
- **When to include**：当 agent 工作时需要参考某些文档时
- **Examples**: `references/finance.md` for financial schemas, `references/mnda.md` for company NDA template, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Examples**：`references/finance.md` 用于财务 schema，`references/mnda.md` 用于公司 NDA 模板，`references/policies.md` 用于公司政策，`references/api_docs.md` 用于 API 规范
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Use cases**：数据库 schema、API 文档、领域知识、公司政策、详细工作流指南
- **Benefits**: Keeps SKILL.md lean, loaded only when the agent determines it's needed
- **Benefits**：保持 SKILL.md 精简，只在 agent 判断需要时加载
- **Best practice**: If files are large (>10k words), include grep or glob patterns in SKILL.md so the agent can use built-in search tools efficiently; mention when the default `grep(output_mode="files_with_matches")`, `grep(output_mode="count")`, `grep(fixed_strings=true)`, `glob(entry_type="dirs")`, or pagination via `head_limit` / `offset` is the right first step
- **Best practice**：如果文件很大（超过 1 万词），在 SKILL.md 中包含 grep 或 glob 模式，使 agent 能高效使用内置搜索工具；说明何时默认使用 `grep(output_mode="files_with_matches")`、`grep(output_mode="count")`、`grep(fixed_strings=true)`、`glob(entry_type="dirs")`，或通过 `head_limit` / `offset` 分页作为正确的第一步
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window. Keep only essential procedural instructions and workflow guidance in SKILL.md; move detailed reference material, schemas, and examples to references files.
- **Avoid duplication**：信息应只存在于 SKILL.md 或参考文件之一，而不是两处都存在。除非信息确实是技能的核心，否则详细信息应优先放入参考文件；这能保持 SKILL.md 精简，同时让信息可被发现且不占用过多上下文窗口。SKILL.md 中只保留必要的程序性说明和工作流指导；将详细参考材料、schema 和示例移到参考文件中。

##### Assets (`assets/`)
资产（`assets/`）

Files not intended to be loaded into context, but rather used within the output the agent produces.
这些文件不打算加载到上下文中，而是用于 agent 生成的输出。

- **When to include**: When the skill needs files that will be used in the final output
- **When to include**：当技能需要最终输出中会使用的文件时
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Examples**：`assets/logo.png` 用于品牌资产，`assets/slides.pptx` 用于 PowerPoint 模板，`assets/frontend-template/` 用于 HTML/React 样板，`assets/font.ttf` 用于排版字体
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Use cases**：模板、图片、图标、样板代码、字体、会被复制或修改的示例文档
- **Benefits**: Separates output resources from documentation, enables the agent to use files without loading them into context
- **Benefits**：将输出资源与文档分离，使 agent 能在不将文件加载到上下文的情况下使用它们

#### What to Not Include in a Skill
技能中不应包含什么

A skill should only contain essential files that directly support its functionality. Do NOT create extraneous documentation or auxiliary files, including:
技能应只包含直接支持其功能的必要文件。不要创建额外文档或辅助文件，包括：

- README.md
- README.md
- INSTALLATION_GUIDE.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- CHANGELOG.md
- etc.
- 等等。

The skill should only contain the information needed for an AI agent to do the job at hand. It should not contain auxiliary context about the process that went into creating it, setup and testing procedures, user-facing documentation, etc. Creating additional documentation files just adds clutter and confusion.
技能应只包含 AI agent 完成当前工作所需的信息。它不应包含关于创建过程、设置和测试步骤、面向用户的文档等辅助上下文。创建额外文档文件只会增加混乱和困惑。

### Progressive Disclosure Design Principle
渐进式披露设计原则

Skills use a three-level loading system to manage context efficiently:
技能使用三级加载系统来高效管理上下文：

1. **Metadata (name + description)** - Always in context (~100 words)
1. **Metadata（name + description）** - 始终在上下文中（约 100 词）
2. **SKILL.md body** - When skill triggers (<5k words)
2. **SKILL.md body** - 技能触发时加载（少于 5000 词）
3. **Bundled resources** - As needed by the agent (Unlimited because scripts can be executed without reading into context window)
3. **Bundled resources** - agent 按需加载（不受限制，因为脚本可以在不读入上下文窗口的情况下执行）

#### Progressive Disclosure Patterns
渐进式披露模式

Keep SKILL.md body to the essentials and under 500 lines to minimize context bloat. Split content into separate files when approaching this limit. When splitting out content into other files, it is very important to reference them from SKILL.md and describe clearly when to read them, to ensure the reader of the skill knows they exist and when to use them.
将 SKILL.md 正文保持在必要内容范围内，并控制在 500 行以下，以尽量减少上下文膨胀。接近此限制时，将内容拆分到单独文件中。将内容拆分到其他文件时，务必在 SKILL.md 中引用它们，并清楚说明何时读取，以确保技能读者知道它们存在以及何时使用。

**Key principle:** When a skill supports multiple variations, frameworks, or options, keep only the core workflow and selection guidance in SKILL.md. Move variant-specific details (patterns, examples, configuration) into separate reference files.
**关键原则：**当技能支持多种变体、框架或选项时，SKILL.md 中只保留核心工作流和选择指导。将变体特定细节（模式、示例、配置）移到单独的参考文件中。

**Pattern 1: High-level guide with references**
**模式 1：带参考资料的高层指南**

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

the agent loads FORMS.md, REFERENCE.md, or EXAMPLES.md only when needed.
agent 仅在需要时加载 FORMS.md、REFERENCE.md 或 EXAMPLES.md。

**Pattern 2: Domain-specific organization**
**模式 2：按领域组织**

For Skills with multiple domains, organize content by domain to avoid loading irrelevant context:
对于包含多个领域的技能，按领域组织内容以避免加载无关上下文：

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

When a user asks about sales metrics, the agent only reads sales.md.
当用户询问销售指标时，agent 只读取 sales.md。

Similarly, for skills supporting multiple frameworks or variants, organize by variant:
类似地，对于支持多个框架或变体的技能，按变体组织：

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

When the user chooses AWS, the agent only reads aws.md.
当用户选择 AWS 时，agent 只读取 aws.md。

**Pattern 3: Conditional details**
**模式 3：条件性细节**

Show basic content, link to advanced content:
展示基础内容，并链接到高级内容：

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

the agent reads REDLINING.md or OOXML.md only when the user needs those features.
只有当用户需要这些功能时，agent 才读取 REDLINING.md 或 OOXML.md。

**Important guidelines:**
**重要指南：**

- **Avoid deeply nested references** - Keep references one level deep from SKILL.md. All reference files should link directly from SKILL.md.
- **Avoid deeply nested references** - 让参考资料相对 SKILL.md 保持一层深度。所有参考文件都应直接从 SKILL.md 链接。
- **Structure longer reference files** - For files longer than 100 lines, include a table of contents at the top so the agent can see the full scope when previewing.
- **Structure longer reference files** - 对超过 100 行的文件，在顶部包含目录，使 agent 预览时能看到完整范围。

## Skill Creation Process
技能创建流程

Skill creation involves these steps:
技能创建包含以下步骤：

1. Understand the skill with concrete examples
1. 通过具体示例理解技能
2. Plan reusable skill contents (scripts, references, assets)
2. 规划可复用的技能内容（脚本、参考资料、资产）
3. Initialize the skill (run init_skill.py)
3. 初始化技能（运行 init_skill.py）
4. Edit the skill (implement resources and write SKILL.md)
4. 编辑技能（实现资源并编写 SKILL.md）
5. Package the skill (run package_skill.py)
5. 打包技能（运行 package_skill.py）
6. Iterate based on real usage
6. 基于实际使用进行迭代

Follow these steps in order, skipping only if there is a clear reason why they are not applicable.
按顺序遵循这些步骤，只有在明确不适用时才跳过。

### Skill Naming
技能命名

- Use lowercase letters, digits, and hyphens only; normalize user-provided titles to hyphen-case (e.g., "Plan Mode" -> `plan-mode`).
- 仅使用小写字母、数字和连字符；将用户提供的标题规范化为连字符形式（例如，"Plan Mode" -> `plan-mode`）。
- When generating names, generate a name under 64 characters (letters, digits, hyphens).
- 生成名称时，生成少于 64 个字符的名称（字母、数字、连字符）。
- Prefer short, verb-led phrases that describe the action.
- 优先使用简短、以动词开头且描述动作的短语。
- Namespace by tool when it improves clarity or triggering (e.g., `gh-address-comments`, `linear-address-issue`).
- 当按工具命名空间有助于清晰度或触发时采用这种方式（例如，`gh-address-comments`、`linear-address-issue`）。
- Name the skill folder exactly after the skill name.
- 技能文件夹名称必须与技能名称完全一致。

### Step 1: Understanding the Skill with Concrete Examples
步骤 1：通过具体示例理解技能

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.
仅当已经清楚理解技能使用模式时才跳过此步骤。即使处理现有技能，此步骤仍然有价值。

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.
要创建有效技能，需要清楚理解技能将如何被使用的具体示例。这种理解可以来自用户直接提供的示例，也可以来自经过用户反馈验证的生成示例。

For example, when building an image-editor skill, relevant questions include:
例如，构建 image-editor 技能时，相关问题包括：

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- “image-editor 技能应支持哪些功能？编辑、旋转，还有其他吗？”
- "Can you give some examples of how this skill would be used?"
- “你能给一些这个技能会如何被使用的示例吗？”
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- “我能想到用户可能会提出‘移除这张图片中的红眼’或‘旋转这张图片’之类的请求。你还能想到这个技能的其他使用方式吗？”
- "What would a user say that should trigger this skill?"
- “用户说什么时应触发这个技能？”

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.
为避免让用户不知所措，不要在单条消息中问太多问题。先从最重要的问题开始，并根据需要继续追问，以提高效果。

Conclude this step when there is a clear sense of the functionality the skill should support.
当已经清楚了解技能应支持的功能时，结束此步骤。

### Step 2: Planning the Reusable Skill Contents
步骤 2：规划可复用的技能内容

To turn concrete examples into an effective skill, analyze each example by:
要将具体示例转化为有效技能，请通过以下方式分析每个示例：

1. Considering how to execute on the example from scratch
1. 思考如何从零开始执行该示例
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly
2. 识别反复执行这些工作流时哪些脚本、参考资料和资产会有帮助

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:
示例：构建 `pdf-editor` 技能来处理“帮我旋转这个 PDF”这类请求时，分析表明：

1. Rotating a PDF requires re-writing the same code each time
1. 旋转 PDF 每次都需要重写相同代码
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill
2. 将 `scripts/rotate_pdf.py` 脚本存储在技能中会很有帮助

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:
示例：为“帮我构建一个待办应用”或“帮我构建一个用于跟踪步数的仪表盘”这类请求设计 `frontend-webapp-builder` 技能时，分析表明：

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
1. 编写前端 webapp 每次都需要相同的 HTML/React 样板
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill
2. 将包含 HTML/React 项目样板文件的 `assets/hello-world/` 模板存储在技能中会很有帮助

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:
示例：构建 `big-query` 技能来处理“今天有多少用户登录？”这类请求时，分析表明：

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
1. 查询 BigQuery 每次都需要重新发现表 schema 和关系
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill
2. 将记录表 schema 的 `references/schema.md` 文件存储在技能中会很有帮助

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.
要确定技能内容，请分析每个具体示例，创建要包含的可复用资源列表：脚本、参考资料和资产。

### Step 3: Initializing the Skill
步骤 3：初始化技能

At this point, it is time to actually create the skill.
此时，就该实际创建技能了。

Skip this step only if the skill being developed already exists, and iteration or packaging is needed. In this case, continue to the next step.
仅当正在开发的技能已经存在且需要迭代或打包时，才跳过此步骤。在这种情况下，继续下一步。

When creating a new skill from scratch, always run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.
从零创建新技能时，始终运行 `init_skill.py` 脚本。该脚本会便捷地生成一个新的模板技能目录，并自动包含技能所需的一切，使技能创建过程更高效、更可靠。

For `nanobot`, custom skills should live under the active workspace `skills/` directory so they can be discovered automatically at runtime (for example, `<workspace>/skills/my-skill/SKILL.md`).
对于 `nanobot`，自定义技能应位于活动工作区的 `skills/` 目录下，以便运行时自动发现（例如，`<workspace>/skills/my-skill/SKILL.md`）。

Usage:
用法：

```bash
scripts/init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]
```

Examples:
示例：

```bash
scripts/init_skill.py my-skill --path ./workspace/skills
scripts/init_skill.py my-skill --path ./workspace/skills --resources scripts,references
scripts/init_skill.py my-skill --path ./workspace/skills --resources scripts --examples
```

The script:
该脚本会：

- Creates the skill directory at the specified path
- 在指定路径创建技能目录
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- 生成带有正确 frontmatter 和 TODO 占位符的 SKILL.md 模板
- Optionally creates resource directories based on `--resources`
- 根据 `--resources` 可选地创建资源目录
- Optionally adds example files when `--examples` is set
- 设置 `--examples` 时可选地添加示例文件

After initialization, customize the SKILL.md and add resources as needed. If you used `--examples`, replace or delete placeholder files.
初始化后，根据需要自定义 SKILL.md 并添加资源。如果使用了 `--examples`，替换或删除占位文件。

### Step 4: Edit the Skill
步骤 4：编辑技能

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of the agent to use. Include information that would be beneficial and non-obvious to the agent. Consider what procedural knowledge, domain-specific details, or reusable assets would help another agent instance execute these tasks more effectively.
编辑（新生成或现有）技能时，请记住该技能是为另一个 agent 实例使用而创建的。包含对 agent 有益且非显而易见的信息。思考哪些程序性知识、领域特定细节或可复用资产能帮助另一个 agent 实例更有效地执行这些任务。

#### Learn Proven Design Patterns
学习经过验证的设计模式

Consult these helpful guides based on your skill's needs:
根据技能需求参考这些有用指南：

- **Multi-step processes**: See references/workflows.md for sequential workflows and conditional logic
- **Multi-step processes**：查看 references/workflows.md，了解顺序工作流和条件逻辑
- **Specific output formats or quality standards**: See references/output-patterns.md for template and example patterns
- **Specific output formats or quality standards**：查看 references/output-patterns.md，了解模板和示例模式

These files contain established best practices for effective skill design.
这些文件包含有效技能设计的成熟最佳实践。

#### Start with Reusable Skill Contents
从可复用技能内容开始

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.
开始实现时，从上面识别出的可复用资源开始：`scripts/`、`references/` 和 `assets/` 文件。请注意，此步骤可能需要用户输入。例如，实现 `brand-guidelines` 技能时，用户可能需要提供品牌资产或模板以存储在 `assets/` 中，或提供文档以存储在 `references/` 中。

Added scripts must be tested by actually running them to ensure there are no bugs and that the output matches what is expected. If there are many similar scripts, only a representative sample needs to be tested to ensure confidence that they all work while balancing time to completion.
新增脚本必须通过实际运行来测试，以确保没有 bug 且输出符合预期。如果有许多相似脚本，只需测试有代表性的样本，以在完成时间和工作信心之间取得平衡。

If you used `--examples`, delete any placeholder files that are not needed for the skill. Only create resource directories that are actually required.
如果使用了 `--examples`，删除技能不需要的任何占位文件。只创建实际需要的资源目录。

#### Update SKILL.md
更新 SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.
**写作指南：**始终使用祈使/不定式形式。

##### Frontmatter
Frontmatter

Write the YAML frontmatter with `name` and `description`:
编写包含 `name` 和 `description` 的 YAML frontmatter：

- `name`: The skill name
- `name`：技能名称
- `description`: This is the primary triggering mechanism for your skill, and helps the agent understand when to use the skill.
- `description`：这是技能的主要触发机制，并帮助 agent 理解何时使用该技能。
  - Include both what the Skill does and specific triggers/contexts for when to use it.
  - 同时包含技能的作用，以及何时使用它的具体触发条件/上下文。
  - Include all "when to use" information here - Not in the body. The body is only loaded after triggering, so "When to Use This Skill" sections in the body are not helpful to the agent.
  - 将所有“何时使用”信息包含在这里，而不是正文中。正文只在触发后加载，因此正文中的“When to Use This Skill”章节对 agent 没有帮助。
  - Example description for a `docx` skill: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when the agent needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
  - `docx` 技能的示例 description：“Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when the agent needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks”

Keep frontmatter minimal. In `nanobot`, `metadata` and `always` are also supported when needed, but avoid adding extra fields unless they are actually required.
保持 frontmatter 简洁。在 `nanobot` 中，也支持按需使用 `metadata` 和 `always`，但除非确实需要，否则避免添加额外字段。

##### Body
正文

Write instructions for using the skill and its bundled resources.
编写使用该技能及其捆绑资源的说明。

### Step 5: Packaging a Skill
步骤 5：打包技能

Once development of the skill is complete, it must be packaged into a distributable .skill file that gets shared with the user. The packaging process automatically validates the skill first to ensure it meets all requirements:
技能开发完成后，必须将其打包为可分发的 .skill 文件并分享给用户。打包过程会先自动验证技能，以确保其满足所有要求：

```bash
scripts/package_skill.py <path/to/skill-folder>
```

Optional output directory specification:
可选的输出目录指定：

```bash
scripts/package_skill.py <path/to/skill-folder> ./dist
```

The packaging script will:
打包脚本会：

1. **Validate** the skill automatically, checking:
1. **Validate** 自动验证技能，检查：
   - YAML frontmatter format and required fields
   - YAML frontmatter 格式和必需字段
   - Skill naming conventions and directory structure
   - 技能命名约定和目录结构
   - Description completeness and quality
   - Description 的完整性和质量
   - File organization and resource references
   - 文件组织和资源引用

2. **Package** the skill if validation passes, creating a .skill file named after the skill (e.g., `my-skill.skill`) that includes all files and maintains the proper directory structure for distribution. The .skill file is a zip file with a .skill extension.
2. **Package** 如果验证通过，则打包技能，创建一个以技能命名的 .skill 文件（例如，`my-skill.skill`），其中包含所有文件并保持适合分发的正确目录结构。.skill 文件是带有 .skill 扩展名的 zip 文件。

   Security restriction: symlinks are rejected and packaging fails when any symlink is present.
   安全限制：符号链接会被拒绝；存在任何符号链接时打包会失败。

If validation fails, the script will report the errors and exit without creating a package. Fix any validation errors and run the packaging command again.
如果验证失败，脚本会报告错误并退出，不会创建包。修复所有验证错误后，再次运行打包命令。

### Step 6: Iterate
步骤 6：迭代

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.
测试技能后，用户可能会请求改进。这通常发生在刚使用技能之后，此时对技能表现仍有新鲜上下文。

**Iteration workflow:**
**迭代工作流：**

1. Use the skill on real tasks
1. 在真实任务中使用技能
2. Notice struggles or inefficiencies
2. 注意遇到的困难或低效之处
3. Identify how SKILL.md or bundled resources should be updated
3. 识别应如何更新 SKILL.md 或捆绑资源
4. Implement changes and test again
4. 实现变更并再次测试
