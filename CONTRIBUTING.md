# Contributing to nanobot

# 为 nanobot 做贡献

Thank you for being here.

感谢你来到这里。

nanobot is built with a simple belief: good tools should feel calm, clear, and humane.
We care deeply about useful features, but we also believe in achieving more with less:
solutions should be powerful without becoming heavy, and ambitious without becoming
needlessly complicated.

nanobot 基于一个简单信念而构建：好的工具应该让人感到平静、清晰且有人情味。我们非常重视实用功能，但也相信以少胜多：解决方案应该强大而不沉重，富有雄心而不过度复杂。

This guide is not only about how to open a PR. It is also about how we hope to build
software together: with care, clarity, and respect for the next person reading the code.

这份指南不仅说明如何提交 PR，也说明我们希望如何一起构建软件：带着认真、清晰，以及对下一位代码读者的尊重。

## Maintainers

## 维护者

| Maintainer<br>维护者 | Focus<br>关注方向 |
|------------|-------|
| [@re-bin](https://github.com/re-bin) | Project lead, `main` branch<br>项目负责人，`main` 分支 |
| [@chengyongru](https://github.com/chengyongru) | `nightly` branch, experimental features<br>`nightly` 分支，实验性功能 |

## Branching Strategy

## 分支策略

We use a two-branch model to balance stability and exploration:

我们使用双分支模型来平衡稳定性与探索性：

| Branch<br>分支 | Purpose<br>用途 | Stability<br>稳定性 |
|--------|---------|-----------|
| `main` | Stable releases<br>稳定版本 | Production-ready<br>生产就绪 |
| `nightly` | Experimental features<br>实验性功能 | May have bugs or breaking changes<br>可能存在 bug 或破坏性变更 |

### Which Branch Should I Target?

### 我应该目标哪个分支？

**Target `nightly` if your PR includes:**

**如果你的 PR 包含以下内容，请目标 `nightly`：**

- New features or functionality<br>新特性或新功能
- Refactoring that may affect existing behavior<br>可能影响现有行为的重构
- Changes to APIs or configuration<br>API 或配置变更

**Target `main` if your PR includes:**

**如果你的 PR 包含以下内容，请目标 `main`：**

- Bug fixes with no behavior changes<br>不改变行为的 bug 修复
- Documentation improvements<br>文档改进
- Minor tweaks that don't affect functionality<br>不影响功能的小调整

**When in doubt, target `nightly`.** It is easier to move a stable idea from `nightly`
to `main` than to undo a risky change after it lands in the stable branch.

**如果不确定，请目标 `nightly`。** 将稳定想法从 `nightly` 移到 `main`，比在风险变更进入稳定分支后再撤销要容易。

### How Does Nightly Get Merged to Main?

### Nightly 如何合并到 Main？

We don't merge the entire `nightly` branch. Instead, stable features are **cherry-picked** from `nightly` into individual PRs targeting `main`:

我们不会合并整个 `nightly` 分支。相反，稳定功能会从 `nightly` 中被 **cherry-pick** 到面向 `main` 的独立 PR 中：

```
nightly  ──┬── feature A (stable) ──► PR ──► main
           ├── feature B (testing)
           └── feature C (stable) ──► PR ──► main
```

This happens approximately **once a week**, but the timing depends on when features become stable enough.

这大约 **每周一次** 发生，但具体时间取决于功能何时足够稳定。

### Quick Summary

### 快速总结

| Your Change<br>你的变更 | Target Branch<br>目标分支 |
|-------------|---------------|
| New feature<br>新功能 | `nightly` |
| Bug fix<br>Bug 修复 | `main` |
| Documentation<br>文档 | `main` |
| Refactoring<br>重构 | `nightly` |
| Unsure<br>不确定 | `nightly` |

## Development Setup

## 开发环境设置

Keep setup boring and reliable. The goal is to get you into the code quickly:

让设置过程保持朴素且可靠。目标是让你快速进入代码：

```bash
# Clone the repository
git clone https://github.com/HKUDS/nanobot.git
cd nanobot

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint code
ruff check nanobot/

# Format code
ruff format nanobot/
```

## Code Style

## 代码风格

We care about more than passing lint. We want nanobot to stay small, calm, and readable.

我们关心的不只是通过 lint。我们希望 nanobot 保持小巧、平静且可读。

When contributing, please aim for code that feels:

贡献时，请尽量编写具有以下特质的代码：

- Simple: prefer the smallest change that solves the real problem<br>简单：优先选择能解决真实问题的最小变更
- Clear: optimize for the next reader, not for cleverness<br>清晰：为下一位读者优化，而不是追求炫技
- Decoupled: keep boundaries clean and avoid unnecessary new abstractions<br>解耦：保持边界清晰，避免不必要的新抽象
- Honest: do not hide complexity, but do not create extra complexity either<br>诚实：不要隐藏复杂性，也不要制造额外复杂性
- Durable: choose solutions that are easy to maintain, test, and extend<br>持久：选择易于维护、测试和扩展的方案

In practice:

实践中：

- Line length: 100 characters (`ruff`)<br>行长度：100 个字符（`ruff`）
- Target: Python 3.11+<br>目标版本：Python 3.11+
- Linting: `ruff` with rules E, F, I, N, W (E501 ignored)<br>Linting：使用 `ruff` 的 E、F、I、N、W 规则（忽略 E501）
- Async: uses `asyncio` throughout; pytest with `asyncio_mode = "auto"`<br>异步：全程使用 `asyncio`；pytest 使用 `asyncio_mode = "auto"`
- Prefer readable code over magical code<br>优先选择可读代码，而不是魔法式代码
- Prefer focused patches over broad rewrites<br>优先选择聚焦补丁，而不是大范围重写
- If a new abstraction is introduced, it should clearly reduce complexity rather than move it around<br>如果引入新抽象，它应当明确降低复杂性，而不是把复杂性移到别处

## Questions?

## 有问题？

If you have questions, ideas, or half-formed insights, you are warmly welcome here.

如果你有问题、想法，或尚未完全成形的洞见，我们都热烈欢迎。

Please feel free to open an [issue](https://github.com/HKUDS/nanobot/issues), join the community, or simply reach out:

欢迎随时提交 [issue](https://github.com/HKUDS/nanobot/issues)、加入社区，或直接联系：

- [Discord](https://discord.gg/MnCvHqpUGB)
- [Feishu/WeChat](./COMMUNICATION.md)
- Email: Xubin Ren (@Re-bin) — <xubinrencs@gmail.com>
  <br>邮箱：Xubin Ren (@Re-bin) — <xubinrencs@gmail.com>

Thank you for spending your time and care on nanobot. We would love for more people to participate in this community, and we genuinely welcome contributions of all sizes.

感谢你愿意把时间和心力投入 nanobot。我们希望更多人参与这个社区，也真诚欢迎各种规模的贡献。
