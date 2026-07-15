# nature-review-studio v1.4.1

**简体中文（默认）** · [English](README_EN.md)

> Nature 风格多视角审稿与回复 Skill，基于 1287 份 Nature 审稿意见 (2025–2026) 蒸馏。

## 一键装机

在 Codex 里说
```powershell
请安装位于 https://github.com/mumdark/nature-review-studio 的 Skill
```

装机脚本会：
- 把 `skill/` 复制到 `$HOME/.codex/skills/nature-review-studio/`
- 把当前目录写入 NRS_ROOT（环境变量 + 持久化到 `skill/.nrs_root`）
- 验证 frontmatter 与 6 个 references 全部就位

## 目录布局

```
nature-review-studio-v1.4.1/
├── README.md
├── README_EN.md
├── RELEASE_NOTES.md
├── RELEASE_NOTES_EN.md
├── install.ps1
├── .gitignore
├── skill/                       # Codex 提示词
├── scripts/                     # 渲染与蒸馏
├── tests/                       # 回归测试
├── knowledge/                   # 蒸馏索引（4 个小 JSON）
├── output/                      # 1 对示例
└── pdfs/.gitkeep                # update 入口占位
```

发布版总体积 **~11 MB**。

## 三个接口

| 接口 | 触发 | 输出 |
|---|---|---|
| `review` | 审稿 / review | `review_<case>_<YYYYMMDD>.docx + .md` |
| `respond` | 回复 / response | `respond_<case>_<YYYYMMDD>.docx + .md` |
| `update` | 入库 / 蒸馏 | 不输出 docx，跑离线管线 |

review 与 respond 永远恰好两个文件，无其他附带产物。

## 蒸馏产物映射

| 蒸馏产物 | 落到 references 哪里 | 作用 |
|---|---|---|
| 12 个 concern axis + 默认严重度 | `skill/references/review-axes.md` | 决定"该问什么" |
| 6 种 manuscript → reviewer set 映射 | `skill/references/review-axes.md` | 决定"派几个审稿人、各管什么" |
| 21 种 response strategy | `skill/references/response-axes.md` | 决定"怎么回" |
| 8 种 action status | `skill/references/response-axes.md` | 决定"任务表状态字段" |

### 1. 12 个 concern axis（审稿问题分类）

**是什么**：审稿人可能问的所有问题的"目录"。skill 从 1287 份 Nature PRF 里人工归类，合并同类、剔除偶然项，得出 12 类。

**为什么是 12 个**：太少了（比如只分"实验/写作"两类）会过于笼统，审稿意见写不出"问到了哪个点"；太多了（几十类）反而无法复用，每类样本量太少。

**实测频次**（扫了 1287 case 的全部评论标签）：

| 12 axis | 1287 PRF 命中次数 |
|---|---|
| experimental-design | 6776 |
| figures-and-tables | 6379 |
| claim-moderation | 3824 |
| novelty-significance | 3185 |
| reproducibility | 2751 |
| writing-clarity | 2513 |
| data-resource-quality | 1153 |
| clinical-validity | 1149 |
| mechanism-evidence | 875 |
| mechanistic-vs-correlative | 516 |
| statistical-rigor | 465 |
| ethical-governance | 83 |

**严重度分布**（`knowledge/index_severity.json`，三档）：

每个 axis 都有 `{major, minor, minor-major}` 三个计数。例如 `experimental-design`：572 major / 5991 minor / 213 minor-major，提示：experimental-design 类问题绝大多数是 reviewer 顺手指出的小事（minor），但仍有 ~9% 属"必须改"的 major。

**示例**：假设审稿人读到你的论文说"我们发现 X 基因敲除后，肿瘤完全消退"，可能问的问题归到不同轴：

| 真实审稿问题 | 归到哪个 axis | 默认严重度 |
|---|---|---|
| X 基因的研究已经被 Nature/Science 在 2022 年报道过类似结论 | novelty-significance | major |
| 怎么证明不是 X 下游的 Y 基因导致肿瘤消退？补一个 rescue 实验 | mechanism-evidence | major |
| 只用了 1 株细胞系，需要 3 株以上 | experimental-design | major |
| n=6 不算 power，补 power analysis | statistical-rigor | major |
| 请上传分析代码 | reproducibility | major |
| 这套机制在病人样本里有没有验证？ | clinical-validity | major |
| 动物伦理号 IRB 没写 | ethical-governance | major |
| 数据库注释文件不全 | data-resource-quality | minor-major |
| 图 3 纵轴应该 0-100% | figures-and-tables | minor |
| 引言写得太啰嗦 | writing-clarity | minor |
| 结论写得太强，完全消退没有 100% 数据支持 | claim-moderation | minor-major |
| 相关 ≠ 因果，建议 hedge | mechanistic-vs-correlative | major |

**默认严重度从哪来**：蒸馏时对 1287 份 PRF 里每条 reviewer comment 做频率统计——出现次数 ≥ 5% 标 major 候选；1–5% 标 minor-major；< 1% 标 minor。

**为什么不固定为 major/minor**：同一类问题在不同论文里严重度不同。比如"数据库注释不全"对一篇数据资源论文是 major，对一篇机制论文是 minor。所以是 major / minor / minor-major 三档，让 skill 根据论文类型再做上下浮动。

### 2. 6 种 manuscript → reviewer set 映射

**是什么**：根据论文的"指纹"（方法类型 + 文章类型），决定派几个审稿人、各自扮演什么角色。

**为什么需要**：Nature 一篇论文通常 2–5 个审稿人，不能随便派。如果派错：临床论文派了"ML 审稿人" → 问了一堆不相关的问题；纯湿实验派了"临床审稿人" → 没法问；Review 论文派 5 个 mechanism 审稿人 → 资源浪费。

**映射表的设计依据**：从 1287 份 PRF 里统计"这类论文 Nature 实际派了几位、什么角度的审稿人"，归纳为 6 种典型 fingerprint：

| 论文指纹 | 派几个 | 各审稿人管什么 |
|---|---|---|
| 纯湿实验机制 | 3 | mechanism / experimental-design / figures |
| 队列 + ML 临床 | 5 | clinical-validity / ml / statistics / ethics / figures |
| 观察 + 理论 | 3 | mechanism / statistical-rigor / writing |
| 大型数据 + 工具 | 4 | data-resource-quality / reproducibility / experimental-design / figures |
| Review / Perspective | 2 | novelty-significance / writing-clarity |
| 混合多方法 | 4–5 | 按需组合 |

**实测方法家族**（`knowledge/index_methods.json`，扫了 1287 case 的全文）：

| 方法家族 | 1287 PRF 命中 case 数 |
|---|---|
| review-theory | 1177 |
| data-resource | 778 |
| ML | 588 |
| wet-lab | 492 |
| omics | 457 |
| imaging | 424 |
| clinical | 413 |
| simulation | 146 |
| unspecified | 20 |

**示例**：你给一篇"CRISPR 筛选 + 单细胞 + 小鼠模型 + 临床队列"的论文，skill 看到 4 种方法都涉及（wet-lab + omics + wet-lab + clinical），自动派 4–5 个审稿人，各管一个角度，而不是机械地"3 个"。

**为什么 review / perspective 只派 2 个**：这类文章本身没新数据，审稿重点是"立论是否站得住"和"是否写清楚"，多派人只会提重复意见。

### 3. 21 种 response strategy（回复策略）

**是什么**：面对审稿人的每条问题，作者可以怎么回的"动作字典"。从 1287 份真实 author response 里挖出来——同一类问题，作者反复用类似的回法。

**为什么需要 21 种**：真实审稿回复不是只有"加实验"和"改文字"两招。从 PRF 里看到有 21 种可区分的"动作"。

**A. 接受/补充类**（承认审稿人指出的问题，加东西）
- acknowledge_and_correct：审稿人发现真实错误 → 直接认错+修
- clarify_existing_content：审稿人误读了原文 → 指出在 Methods §2.3 已写
- add_textual_explanation：解释应放正文，不放 response letter
- add_reference：补一篇漏引的关键文献
- add_method_detail：Methods 写得太简，补细节
- add_statistical_analysis：在已有数据上补跑一个统计
- add_robustness_analysis：敏感性分析、bootstrap、alternative model
- add_control：补一组对照实验
- add_experiment：全新湿实验/临床实验
- add_validation_dataset：独立 cohort / 外部验证集
- provide_data_or_code：上传匿名数据/代码

**B. 限制/调整类**（降低强度，而不是补东西）
- moderate_claim：结论写太满，加 hedging（"suggest" 改 "indicate"）
- change_terminology：改一两个 over-strong 的词
- restructure_figure：重组图/表
- move_content_to_supplement：内容降到 SI 节省正文空间
- withdraw_claim：完全删掉站不住的 claim

**C. 拒绝/委托类**（不同意或交编辑）
- explain_infeasibility：实在做不了，说明原因（资源/时间/伦理）
- respectfully_disagree：审稿人真错了，礼貌反驳 + 证据
- request_editor_adjudication：审稿人之间冲突 → 请编辑仲裁
- defer_to_future_work：真实但超出范围，放 future work

**为什么 design 21 这个粒度**：太粗（只 4–5 种）→ 没法精确指派任务，任务表里都写"其他"，看的人不知道作者要做什么；太细（几十种）→ 不同审稿人/编辑口径不一致，同一动作被起不同名。21 是 1287 份 PRF 抽象出来的最大公约数，既覆盖所有真实动作，又能让 skill 写 JSON payload 时直接选一个 label。

### 4. 8 种 action status（任务状态）

**是什么**：任务表里"这条 review 改了吗？改到什么程度？"的状态机。

**为什么需要 8 个状态**：Nature 修回信要追踪每条 review 是真的改完了、还是只写了"我们改好了"但其实没改、还是没改。8 个状态是真实 PRF 里作者回复 + 编辑后续追踪里出现过的所有可能。

| 状态 | 含义 | 触发条件 |
|---|---|---|
| DONE | 改完了，且改在 revised manuscript 里可见 | 用户提供 revised MS，文本匹配 |
| DRAFTED | 改完了，但还没在 revised MS 里看到 | 用户口头说"已改"，但没传 MS |
| TODO_TEXT | 需要改文字 | 策略是 add_textual_explanation 等 |
| TODO_ANALYSIS | 需要跑分析 | 策略是 add_statistical_analysis 等 |
| TODO_EXPERIMENT | 需要做实验 | 策略是 add_experiment 等 |
| TODO_AUTHOR_CONFIRM | 建议改，但要作者确认 | skill 判断拿不准 |
| NOT_FEASIBLE | 真做不了 | 策略是 explain_infeasibility |
| PROPOSED_DISAGREEMENT | 建议礼貌反驳 | 策略是 respectfully_disagree |

## 渲染双输出契约

- review / respond 必产恰好两个文件：`.docx` + 同 stem 的 `.md`
- .md 是审稿内容/回复的纯文本镜像，无任何额外批注块
- Word 字体：走系统默认（Calibri / Microsoft YaHei 由 Office 自动匹配），不在 docx 里硬编码字体
- 加粗策略：只用于标题、表头、置信度行、任务表 ID 列、证据锚点引用，其它正文全部非粗
- 不输出"前言与合规说明"、"主张→证据映射"、"覆盖范围说明"、"对抗性自检"、"分歧/严重程度升级/编辑决定"等内部块（这些只在 skill 内部跑，不进文件）

## 知识库规模

- **1287 case 蒸馏总览**：
  - 12 axis 实测频次（`knowledge/index_axes.json`）—— 与 references 12 axis 名完全一致
  - 9 个方法家族实测频次（`knowledge/index_methods.json`）—— 从 1287 case 全文扫出
  - 12 axis × 3 档严重度分布（`knowledge/index_severity.json`）—— 从评论文本分类
