# micro-harness 🎯

**一个你30分钟就能读完的最小Agent Harness——以及我们如何从17%通过率一路迭代到50%的真实故事。**

[English](README.md) | 简体中文

Claude Code源码泄漏（2026年3月31日）之后，我们了解到**包裹LLM的"外壳"（harness）比模型本身更重要**。斯坦福的Meta-Harness实验表明，同一个模型搭配不同harness，性能差距可达6倍。

但生产级harness太复杂了。Claude Code有51万行TypeScript。这个项目只有约400行Python。

## 真实的Benchmark结果（不吹牛）

我们用**DeepSeek-V3.2**跑了6个困难编码任务，使用自然语言提示词——不手把手教步骤。每个任务跑**3次**测试稳定性。

### 诚实的数字

```
任务          3次通过率      状态
─────────────────────────────────────
代码分析      3/3  (100%)    ✓ 稳定通过
调试修复      3/3  (100%)    ✓ 稳定通过
功能添加      2/3  (67%)     ✓ 基本可靠
测试生成      1/3  (33%)     ✗ 不稳定
代码重构      0/3  (0%)      ✗ 失败
Bug修复      0/3  (0%)      ✗ 失败

可靠通过（≥2/3）: 3/6 = 50%
```

### 迭代历程（17% → 50%）

| 轮次 | 改动 | 结果 | 学到了什么 |
|------|------|------|-----------|
| 0 | 裸跑——无任何优化 | 1/6 (17%) | 大部分任务撞了轮次上限 |
| 1 | 加规划prompt，提高max_turns到20 | 2/6 (33%) | 规划有帮助但不够 |
| 2 | 加模糊编辑提示，更智能的错误信息 | 4/6 (67%) | **编辑恢复是最大突破**——exact match失败时展示附近文本 |
| 3 | 手把手写步骤的prompt | 5/6 (83%) | 但这是"教考试"——作弊了 |
| 4 | 声称"100%通过" | 6/6 | **在骗自己**——换了更简单的任务且只跑了1次 |
| 5 | 诚实重测：自然语言prompt，每个跑3次 | 3/6 (50%) | **这才是真实数字** |

### 真正起作用的改进

1. **安装ripgrep** (+15%) — grep工具每次调用都报错因为`rg`没装。模型白浪费3-5轮绕弯。教训：**harness的好坏取决于它的运行环境。**

2. **模糊编辑提示** (+10%) — 当`old_string`匹配不上时，不是光说"没找到"，而是显示最接近的那一行。模型可以复制精确文本重试。教训：**帮助模型从错误中恢复，而不是只报告错误。**

3. **精简系统prompt** (+8%) — 删掉空话。真正管用的规则只有这几条：
   - "用grep找东西，永远不要读整个文件"
   - "read时用start_line+limit，最多30行"
   - "写完代码立刻运行"

4. **每次恢复干净状态** (+5%) — 之前的agent运行留下了修改过的文件，干扰后续运行。教训：**agent状态污染是测试harness的真实问题。**

### 没用的改进（或者起了反作用）

- **环境预热(bootstrap)** — 给每次prompt增加了tokens但没减少轮次。模型本身就会跑`ls`和`which python3`。
- **文件索引** — 同上。小项目里模型找文件不需要索引。
- **啰嗦的规划prompt** — "每步之前先想清楚"听起来好但DeepSeek直接无视，上来就调工具。

### 仍然失败的原因

**重构 (0/3):** "让它可配置"太抽象。模型不知道应该：(1)加一个dataclass字段 (2)grep找硬编码值 (3)逐个替换。这是**模型理解能力的上限**，不是harness问题。

**Bug修复 (0/3):** "修复错误处理"需要理解`tool_grep`的返回值和agent循环中`tool_result`构造之间的关系。模型读了代码但连不上跨200行的逻辑。

**测试生成 (1/3):** 时灵时不灵。失败时是因为模型搞错了import路径。harness层面的修复：自动把项目根目录注入PYTHONPATH。

## 8个技术点

| # | 技术 | 代码量 | 实测效果 |
|---|------|--------|---------|
| 1 | **Agent循环** — ReAct工具调用循环 | 40行 | 基础 |
| 2 | **工具系统** — 6个结构化工具 > shell | 60×6行 | 必要条件 |
| 3 | **缓存边界** — 稳定前缀 + 动态后缀 | 20行 | 多轮对话省87%成本 |
| 4 | **环境预热** — Meta-Harness的杀手锏 | 30行 | 小项目无效果 |
| 5 | **三层记忆** — 按需加载skill | 50行 | 大项目省95% context |
| 6 | **熔断器** — 每个循环加保险丝 | 15行 | 防止烧钱 |
| 7 | **安全审核** — bash执行前检查 | 40行 | 100%拦截危险命令 |
| 8 | **模糊编辑恢复** — 失败时展示附近文本 | 25行 | **+10%通过率** |

注意：技术3-5在大项目和长会话中才有意义。在我们的小benchmark上没有显著效果。这是诚实的——我们只报告能证明的。

## 快速开始

```bash
git clone https://github.com/wang2-lat/micro-harness.git
cd micro-harness
pip install anthropic openai google-genai

# 离线测试（不需要API key）
python3 benchmarks/test_offline.py

# 用DeepSeek（通过任何OpenAI兼容API）：
OPENAI_API_KEY=你的key OPENAI_BASE_URL=https://api.xxx.com/v1 \
MODEL=DeepSeek-V3.2 python3 src/openai_harness.py "你的任务"

# 用Gemini（免费）：
GEMINI_API_KEY=你的key python3 src/gemini_harness.py "你的任务"

# 子agent模式（规划+执行分离）：
python3 src/dual_agent_harness.py "你的任务"
```

支持3种后端：Anthropic Claude、Google Gemini、任何OpenAI兼容API（DeepSeek、GLM、Kimi等）。

## 示例：FinFars — 金融研究垂直Harness

`examples/finfars.py` 把通用工具替换成领域专用工具：

```bash
python3 examples/finfars.py AAPL
# → 8段式投研报告，真实SEC+雅虎财经数据
```

领域工具：`fetch_filing`（SEC EDGAR）、`fetch_company_facts`、`fetch_stock_price`（雅虎）、`search_news`、`compute_metrics`。全免费API。

## 架构

```
用户任务
    │
    ▼
┌──────────────────────────┐
│  系统Prompt组装           │
│  ┌────────────────────┐  │
│  │ 稳定前缀（缓存）    │  │ ← 技术3
│  │ + 文件索引（L1）    │  │ ← 技术5
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │ 动态后缀（每次）    │  │
│  └────────────────────┘  │
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│   Agent循环               │ ← 技术1
│   for turn in max_turns:  │ ← 技术6（熔断）
│     response = llm(msgs)  │
│     if 完成: break        │
│     for tool in calls:    │
│       安全检查(tool)       │ ← 技术7
│       result = 执行()     │ ← 技术2
│       if 编辑失败:         │
│         展示附近文本()     │ ← 技术8（恢复）
│       msgs.append(result) │
└──────────────────────────┘
```

## 子Agent架构（实验中）

```
用户: "让截断长度可配置"
        │
        ▼
  ┌─── 规划Agent ───┐
  │  读代码，理解结构  │
  │  输出具体步骤列表  │
  └────────────────┘
        │
        ▼
  1. 在HarnessConfig加max_tool_output字段
  2. grep找所有[:10000]
  3. 逐个替换为self.config.max_tool_output
  4. 验证能正常import
        │
        ▼
  ┌─── 执行Agent ───┐
  │  逐步执行        │
  │  每步最多8轮     │
  └────────────────┘
        │
        ▼
  ┌─── 验证Agent ───┐
  │  检查最终结果     │
  └────────────────┘
```

## 我们尝试过但失败的方案（诚实记录）

我们试了3种方案想攻克剩下3个任务。全部失败了。

| 方案 | 做了什么 | 结果 | 为什么失败 |
|------|---------|------|-----------|
| **换模型** | Gemini 2.5 Flash | 0/3 | 更快但不更聪明，bugfix 3轮就放弃了 |
| **子Agent** | 规划Agent + 执行Agent | 0/3 | 规划Agent读了大量代码但生成的步骤太模糊 |
| **加轮数** | max_turns提到25 | 0/9 | 更多轮次=更多无效试错 |

**真正的结论：** 这3个任务（抽象重构、跨函数bugfix、稳定测试生成）超出了DeepSeek-V3.2和Gemini 2.5 Flash的能力边界。可能需要Claude Sonnet/Opus级别的推理能力，或者根本不同的harness架构（代码图谱+符号推理）。

**50%可靠通过率是这个模型+harness组合的诚实天花板。**

## 未解决的问题

剩下3/6的失败是真正的开放问题：

1. **抽象任务分解** — 如何让模型理解"让它可配置"意味着什么步骤
2. **跨函数推理** — 如何帮助模型连接200+行代码中的逻辑
3. **稳定的测试生成** — 自动PYTHONPATH注入、import解析

欢迎PR。

## 许可

MIT

## 延伸阅读

- [Meta-Harness论文 (arXiv 2603.28052)](https://arxiv.org/abs/2603.28052)
- [OpenHarness — 港大学术参考](https://github.com/HKUDS/OpenHarness)
- [Claude Code系统prompt（泄漏版）](https://github.com/Piebald-AI/claude-code-system-prompts)
- [长运行Agent的有效Harness — Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Harness Engineering — Martin Fowler](https://martinfowler.com/articles/harness-engineering.html)
