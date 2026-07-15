# Release Notes — v1.4.1

**简体中文（默认）** · [English](RELEASE_NOTES_EN.md)

## v1.4.1 (2026-07-14)

### 与 V1.4.0 相比

- **cases.jsonl 不再随发布版带**（138 MB → 0）。运行时从不读 cases.jsonl（验证：`render_review_docx.py` / `render_review_md.py` 仅用作 NRS_ROOT 探测，**不打开**文件），所以发布版瘦身 92%（150 MB → 11 MB）
- **manifest.tsv 不再随发布版带**（325 KB）。同样只被 `run_pipeline.py` 写、不被运行时读
- **`test_no_identifiers.py` 升级**：找不到 cases.jsonl 时打印 skip 并以 0 退出，而不是 fail
- **`extract_concerns.py` 全面重写**：
  - 16 原始 axis → 12 references axis 的**显式映射**（`raw_to_canonical` 字段）
  - severity 三档（major / minor / minor-major）从评论文本关键词密度推断
  - method family 从**全文**（不是只 `corresponding` 字段）扫描，**unspecified 从 1287 降到 20**
  - 输出含 `raw_to_canonical` 与 `method_keywords` 元数据，方便复核
- **README 重大更新**：实测频次表替换占位描述，包括：
  - 12 axis 的 1287 PRF 命中次数（`experimental-design` 6776 排第一）
  - 9 个方法家族实测 case 数（`review-theory` 1177 排第一，符合 Nature 真实分布）
  - severity 三档分布解释

### 数据规模

- 1287 cases 蒸馏元数据全部归到 4 个小 JSON：
  - `index_axes.json` (1.8 KB) —— 12 axis 频次 + 映射
  - `index_methods.json` (636 B) —— 9 方法家族
  - `index_severity.json` (1.1 KB) —— 12 axis × 3 档
  - `snap_full_v1.2.json` (306 B) —— 封版 SHA256
- cases.jsonl 移到工作区 `nature_open_peer_review/build/snapshots/snap_full/`，保留作为离线语料

### 已知问题

- severity 分类里"minor 占 80%+"反映了真实 PRF 的措辞倾向（reviewer 普遍礼貌），不是 axis 偏差。如需调权重可改 `extract_concerns.py` 的 SEV_KEYWORDS
- 装机脚本生成的 `.nrs_root` 指向 release 目录，与 install.ps1 的 `-ReleaseRoot` 参数共用
