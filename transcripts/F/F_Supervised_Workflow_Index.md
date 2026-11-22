# 监督阶段索引

整理：F｜日期：2026-11-23

本索引按“需求分类→候选方案生成与评估→编码前计划审批→构建→合规验证→证据驱动修订”定位真实会话。本 PR 的 F 五份会话来自本机原生完整导出（逐字节原样复制）；其他成员的记录以固定提交链接引用，保留原成员、消息角色和决定归属。本索引是阅读导航，不代替会话正文，也不单独证明导出完整性。

## 1. 监督阶段与真实干预

| 阶段 | 学生成员的干预及理由 | 真实会话位置 | 可观察结果与证据边界 |
| --- | --- | --- | --- |
| **需求分类与验收条件** | A 要求分离需求 ID/测试 ID，补需求类型、MoSCoW、取舍和可测 fit criterion；F 要求 O6 用受控数值、身份边界和披露作为验收条件 | A：[O1 会话 L1023–1036][a-classify]；F：[O6 用户回合](CS5351_O6.json#L27458)、[Registry 反馈修订](CS5351_O6.json#L29443)；注释 F-O6-01 | A 后续修订草稿；F 形成可观察统计断言和需求映射。草稿修订不是功能测试通过，也不冒充批准。 |
| **候选方案生成与局部评估（历史）** | A 先限定只读分析，要求最小修复、文件范围与风险；代理比较按指标/按日期 guard、全帧判断风险及更大范围的下载窗口修复 | A：[O1 只读任务 L64–85][a-inspect]、[方案与取舍 L232–286][a-options]；会话 `ses_e34f21c97ffevLFn0o9TxQa9zG` | 有真实的 O1 局部方案建议、风险和范围取舍。它不是全系统多个架构候选的量化评估；不把局部设计放大成整套系统从零架构设计。 |
| **架构文档生成与方案比较（收尾）** | C 指示生成 blueprint、ADR、memory、permissions、runtime policies 和 evaluation table；要求区分历史实际考虑与收尾分析，不编造分数、收益或审批 | C：[架构会话 seq 23011][c-generate]（消息 `msg_203152a7b001UdJbctrWYOHGUW`）；[候选评估表][c-evaluation] | 真实会话含架构文档生成与修订过程。该阶段发生在收尾，不能倒填为首次实现之前的系统候选生成与选择；评估表明确区分 H（历史记录）和 A（收尾分析）。 |
| **编码前计划与人工批准** | A 要求执行计划严格映射获批需求/测试，并在只读阶段停止；随后明确允许三文件内 tests-first 实现。F 要求 O6 先给 A 审执行计划，并核实既有 PR #6 范围 | A：[计划限界 L3118–3130][a-plan]、[允许实施 L3957–3963][a-authorize]、[v1.1 批准 L4328–4336][a-build-approval]；F：[O6 只读执行计划](CS5351_O6.json#L28795)、[编码前核查](CS5351_O6.json#L32312) | 显示“先计划、等待批准、再允许构建”的真实指令。A 会话还保留 Plan/Build 模式切换受限的实际响应；用户说批准不等于代理已经执行。审批有效性须结合原始 PR、计划版本及实际首次编辑时间，不能只据索引判定。 |
| **构建与文件范围控制** | A 限定 market.py、snapshot.py 和 O1 测试文件，先写测试再实现；F 只允许发布 #37 已完成修复，禁止扩大实现 | A：[Build 指令 L4371 起][a-build]及后续写入/修复记录；F：[CI 发布限定](CI_Gate.json#L171589)，注释 F-CI-01 | A 会话提供代码/测试构建过程；F 段是已完成成果的发布监督，不称作首次实现。代理生成内容、工具操作和学生审批分别记录。 |
| **构建后的测试与合规验证** | A 要求报告真实 node ID、测试和 lint；F 要求真实审批核验、不得补造审批，并以受控 PR 验证红灯阻断和修复恢复 | A：[O1 失败后核验 L4934 起][a-test-fix]及后续命令结果；F：[审批闭合](CI_Gate.json#L174064)、[E2 调整](CI_Six_Gates.json#L12840)、[E5 恢复](CI_Six_Gates.json#L15314)，注释 F-CI-02、F-VERIFY-02/03 | 分别提供功能验证、审批门禁和保护行为证据。#41 E1/E2/E4/E5 完成后关闭未合并；E3 未执行。CI 成功、配置 required、实际阻断是不同结论。 |
| **测试证据驱动的实现/测试修订** | A 在 14 passed/2 failed 后指出日期窗口与错误 shuffle fixture，要求在原三文件范围修正并重跑；F 纠正 Unknown 显示与演示输出取证方式 | A：[O1 失败→修正指令 L4934–4938][a-test-fix]及后续实际修复；F：[Unknown 修正计划](CS5351_O6.json#L34154)、[真实捕获输出与网络保护](O6_batch1.json#L78531)，注释 F-O6-03、F-DEMO-03 | 有测试/证据导致实现、测试或验证方法调整的真实链路。O1 两项问题包含测试 fixture 错误；不能称作全部由生产缺陷或架构缺陷导致。 |
| **验证证据驱动的架构文档修订** | C 根据 F 的节点/CI/阻断核对意见补追踪表，再同步七份架构文档，纠正 S5 状态、治理证据缺失和过度覆盖表述 | C：[追踪表修订 seq 23636][c-trace-revise]→[完成回应 seq 23913][c-trace-result]；[七文档同步 seq 23922][c-arch-revise]→[完成回应 seq 24300][c-arch-result] | 存在真实的“证据→学生纠偏→代理修订→检查”过程；此处是架构描述/追踪材料修订，**不是证实生产架构被重新设计**。完整架构演进结论仍需当时设计变更的会话、代码差异和 ADR 支持。 |

## 2. 五份 F 会话怎样共同使用

| 会话 | 索引中的主要作用 | 配套干预注释 |
| --- | --- | --- |
| [CS5351_O6](CS5351_O6.json) | 需求、可测验收点、批准范围、编码前核查、Unknown 修正计划 | F-O6-01～03 |
| [CI_Gate](CI_Gate.json) | 修复发布范围、真实审批记录与闭合 | F-CI-01～02 |
| [CI_Test_Approval](CI_Test_Approval.json) | 拒绝仅凭 CI 标签放行，限定授权边界，保留流程偏差 | F-AUTH-01～02 |
| [CI_Six_Gates](CI_Six_Gates.json) | 对验证方案的停止、引导、重新授权及阻断/恢复证据 | F-VERIFY-01～04 |
| [O6_batch1](O6_batch1.json) | 测试排除项归因纠正、演示命令修订和真实输出取证 | F-DEMO-01～03 |

上述 14 条干预的“位置—原因—指令—结果”见 [F_Intervention_Annotations.md](F_Intervention_Annotations.md)。读取时先看对应 User 消息，再看代理响应、工具调用及实际结果；不要把用户要求当成执行已经成功。

## 3. 借用的其他成员真实会话

| 来源 | 固定提交/位置 | 来源性质与责任归属 |
| --- | --- | --- |
| A 的 O1 会话 | [PR #44](https://github.com/Caicys297/TradingAgents-CS5351/pull/44)，`169588694ca4f6b8f94960e9f5ab9ec0b90bd24c`；`transcripts/A-O1-OpenCode-Session-annotated.md` | 已读取正文。文件说明其将同一会话的两个导出按时间合并，仅移除重复重叠，原消息/工具输出保留；A 的 Student annotation 单独标识。这里引用真实发布文件及其说明，不将其改称 F 会话，也不独立保证它与原数据库逐条一致。该来源现已通过 #44 合并为 `2eb77a4188954f5f671f924dbebca7294738c13f`。 |
| C 的架构文档会话 | [PR #45](https://github.com/Caicys297/TradingAgents-CS5351/pull/45)，`f1bf7b993b024e17dfa4e92c8ca98387632aae78`；`transcripts/C-architecture-docs-session-export.json` | 已读取真实 JSON 消息。会话 ID `ses_e3156feceffeB6Oza74L3gXwQ3`，225 条消息，seq 22773–24541；文件声明按本次工作筛选并脱敏、顺序/角色/措辞保留。不是完整未处理会话，也不是第一次实现前的设计记录。核对时为开放 PR 的文件，不能称为已进入 main。 |

C 会话的具体定位采用固定提交的 JSON 行号，以及 `seq`、消息 ID 和时间交叉核对；A 会话采用固定 Markdown 行号。两者都不会因 F 的本地文件重新排版而变化。这里仅引用，未替其他成员重写或复制其会话。

## 4. 对完整监督流程的覆盖边界

- 目前可以定位：需求分类、局部候选方案取舍、编码前计划与批准、实际构建、测试及合规验证、失败后的实现/验证纠错、架构文档据证修订。
- **尚不能据此证明：**从零生成整套系统的多个架构候选、在首次实现前完成全系统候选评估，以及测试驱动的生产架构重设计。C 的收尾比较和文档修订不能替代缺少的早期过程。
- 如 A/C/B/D/E 另有早期架构设计或架构变更会话，只需给出真实文件/会话 ID、候选片段、评价准则、学生决定及后续实现/测试位置，即可继续补入本索引；不补造历史讨论、不为补材料新增开发。
- 会话文件是否完整、是否未经处理，须按其实际来源单独核对；本索引只提供阶段与干预位置，不作整体合规背书。本索引不修改本机原始会话；GitHub 中五份 JSON 与本机原生导出逐字节一致。

[a-inspect]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L64
[a-classify]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L1023
[a-options]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L232
[a-plan]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L3118
[a-authorize]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L3957
[a-build-approval]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L4328
[a-build]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L4371
[a-test-fix]: https://github.com/Caicys297/TradingAgents-CS5351/blob/169588694ca4f6b8f94960e9f5ab9ec0b90bd24c/transcripts/A-O1-OpenCode-Session-annotated.md#L4934
[c-generate]: https://github.com/Caicys297/TradingAgents-CS5351/blob/f1bf7b993b024e17dfa4e92c8ca98387632aae78/transcripts/C-architecture-docs-session-export.json#L1513
[c-trace-revise]: https://github.com/Caicys297/TradingAgents-CS5351/blob/f1bf7b993b024e17dfa4e92c8ca98387632aae78/transcripts/C-architecture-docs-session-export.json#L5567
[c-trace-result]: https://github.com/Caicys297/TradingAgents-CS5351/blob/f1bf7b993b024e17dfa4e92c8ca98387632aae78/transcripts/C-architecture-docs-session-export.json#L7322
[c-arch-revise]: https://github.com/Caicys297/TradingAgents-CS5351/blob/f1bf7b993b024e17dfa4e92c8ca98387632aae78/transcripts/C-architecture-docs-session-export.json#L7355
[c-arch-result]: https://github.com/Caicys297/TradingAgents-CS5351/blob/f1bf7b993b024e17dfa4e92c8ca98387632aae78/transcripts/C-architecture-docs-session-export.json#L9914
[c-evaluation]: https://github.com/Caicys297/TradingAgents-CS5351/blob/f1bf7b993b024e17dfa4e92c8ca98387632aae78/docs/architecture/evaluation-table.md#L18
