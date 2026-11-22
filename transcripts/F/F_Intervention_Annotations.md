# F — OpenCode 会话干预注释

整理：F｜2026-11-23

本文件独立于原生 JSON 会话正文，提供 14 条实际用户干预的原因、约束和可观察结果。用户消息已逐条定位到本机原生完整导出中的消息 ID；链接行号指本 PR 的 JSON。注释为事后整理，不是代理原始消息，不把提出要求当作执行完成，也不把工具执行改称人工执行。转达 A/B/C 决定时保留原决定者身份。

## F-CI-01：限定修复和发布范围

- **干预位置：** [20261122_session_transcripts_CI_Gate.md，用户回合](CI_Gate.json#L171589)；消息 ID `msg_1ff64d790001maKXMPk58RXoWQ`。
- **原文定位：** `Publish the already completed PR #37 reviewed-gap fixes`
- **原因：** 仅发布既有权限修复、真实负例和会话证据，避免扩大实现或覆盖其他工作。
- **F 的指令：** 限定文件及现有分支；保留审批红灯，不强推、不改写历史。
- **可观察结果：** 后续 Published 回复记录 3314d52、两份代码修复及证据发布；权限测试 21 passed。
- **结果定位：** 同一原生导出内搜索 `Published. PR #37 remains Draft`。

## F-CI-02：要求用真实审批闭合门禁

- **干预位置：** [20261122_session_transcripts_CI_Gate.md，用户回合](CI_Gate.json#L174064)；消息 ID `msg_20132fa27001SG4FDZ9sEE1Fiv`。
- **原文定位：** `Close PR #37’s approval gate following A’s explicit instruction`
- **原因：** 旧规则和 O4 分类不匹配，不能以迁移例外替代本批审批。
- **F 的指令：** 正常同步 main；按 #35 原始计划、时间、范围核验 CI 批次记录，禁止倒填审批。
- **可观察结果：** 后续记录 1c0b740，两份审批均接受，CI 44979161445 success；不是靠复用 #38 例外通过。
- **结果定位：** 同一原生导出内搜索 `PR #37's approval gate is closed`。

## F-AUTH-01：拒绝仅凭 CI 标签取得审核授权

- **干预位置：** [20261122_session_transcripts_CI_Test_Approval.md，用户回合](CI_Test_Approval.json#L6347)；消息 ID `msg_1ff3e21d3001MMEQYwpwlmnJ4a`。
- **原文定位：** `Fix one authorization-boundary defect in PR #38`
- **原因：** 仅检查自声明标签不足以证明实施者身份及 CI/治理范围。
- **F 的指令：** 增加可信 F 身份、实际变更和固定批准范围核验，保留自批及时间限制。
- **可观察结果：** 后续记录 fd798b4；75 passed、Ruff 通过，并记录负例依赖新增边界检查。
- **结果定位：** 同一原生导出内搜索 `**Tests/lint:**`。

## F-AUTH-02：保留历史偏差，补真实证据

- **干预位置：** [20261122_session_transcripts_CI_Test_Approval.md，用户回合](CI_Test_Approval.json#L10670)；消息 ID `msg_1ff523b62001ap539rIHCZf0ht`。
- **原文定位：** `Complete A’s requested evidence-only cleanup on PR #38`
- **原因：** AI-use 缺口与编码前记录缺失是不同问题，不能补造审批追求全绿。
- **F 的指令：** 仅补真实导出和日志，保留 Test Approval 失败及实际时间线，交 A 决定。
- **可观察结果：** 后续记录证据提交 6b3223b 已正常推送，停在独立审核；A 后来的例外处置不倒算为事前审批。
- **结果定位：** 同一原生导出内搜索 `Evidence-only cleanup complete`。

## F-VERIFY-01：要求先核对实际门禁语义

- **干预位置：** [20261122_session_transcripts_CI_Six_Gates.md，用户回合](CI_Six_Gates.json#L10739)；消息 ID `msg_2019f08370019EaNdBcX6MnKIb`。
- **原文定位：** `Continue the authorized E2/E5 branch-protection verification`
- **原因：** 逐提交 Ruff 的坏提交可能在 HEAD 修好后仍失败，试验须可正常恢复。
- **F 的指令：** 读取实际检查器、选择可逆故障；无法隔离就报告，不修改门禁掩盖问题。
- **可观察结果：** 会话查明 Schema 与回归矩阵耦合，停止发布并报告，未冒称单 job 隔离完成。
- **结果定位：** 同一原生导出内搜索 `I stopped before publishing E2`。

## F-VERIFY-02：根据证据调整试验口径

- **干预位置：** [20261122_session_transcripts_CI_Six_Gates.md，用户回合](CI_Six_Gates.json#L12840)；消息 ID `msg_201b527c10016jiS6K7VLaOQ29`。
- **原文定位：** `Resume E2/E5 using A’s latest confirmation`
- **原因：** 一处 Schema 故障会造成多个关联检查失败，旧口径过严。
- **F 的指令：** 取得 A 明确允许后，如实验证失败检查阻断，保留先前证据及提交历史。
- **可观察结果：** 后续 E2 executed 记录 857e762、Schema 加四矩阵失败，其余 12 项通过；因缺新 Review 停止，不提前宣称单独阻断已证。
- **结果定位：** 同一原生导出内搜索 `E2 executed; now stopped`。

## F-VERIFY-03：恢复原文件且禁止提前关闭试验

- **干预位置：** [20261122_session_transcripts_CI_Six_Gates.md，用户回合](CI_Six_Gates.json#L15314)；消息 ID `msg_2020e2df50014DhIOgJkCikLPE`。
- **原文定位：** `Continue E5 in the existing PR #41 worktree`
- **原因：** 新提交会使旧审批失效，恢复文件不等于恢复合并资格。
- **F 的指令：** 逐字节恢复并正常追加提交；等 CI 和新 Review，保持 PR OPEN。
- **可观察结果：** 后续记录恢复提交 9462d6c 和原始哈希一致；推送因网络失败而停止。最终成功推送/Review/关闭属于外部核验材料，不能把此处失败改成成功。
- **结果定位：** 同一原生导出内搜索 `E5 restoration is complete locally`。

## F-VERIFY-04：区分实现、CI 与强制阻断证据

- **干预位置：** [20261122_session_transcripts_CI_Six_Gates.md，用户回合](CI_Six_Gates.json#L17523)；消息 ID `msg_2024197fa001VQI69sqDOzdAo0`。
- **原文定位：** `Finalize the existing six-gate CI audit and handoff package`
- **原因：** 历史报告不能直接代表最终版本，且 CI 全绿并不自动证明所有检查被设 required。
- **F 的指令：** 汇总已合并成果、固定 SHA 和试验结论，保留 E3 未执行及 S6 终止边界。
- **可观察结果：** 后续生成最终交接和索引，列明管理员配置证据当时仍缺；之后截图已归档属于后续补充，不改写该历史状态。
- **结果定位：** 同一原生导出内搜索 `Final handoff and index written`。

## F-O6-01：将验收条件变成可观察断言

- **干预位置：** [20261122_session_transcripts_CS5351_O6.md，用户回合](CS5351_O6.json#L27458)；消息 ID `msg_1df22ec0d0012AX4DOeI8r041Z`。
- **原文定位：** `Update only O6-Test-Plan-v0.1-DRAFT.md.`
- **原因：** 调用次数、token、耗时及身份披露不能只写成笼统功能目标。
- **F 的指令：** 指定 TC-O6-07 的受控耗时和统计行，TC-O6-12 的两条披露；保持 Draft，不写代码。
- **可观察结果：** 会话中产生计划文档改动，要求保留 Pending/Planned 状态；这里只能作为计划修订证据，不算功能执行通过。

## F-O6-02：避免伪造批准版本

- **干预位置：** [20261122_session_transcripts_CS5351_O6.md，用户回合](CS5351_O6.json#L30514)；消息 ID `msg_1e27eb402001UD5SqijSqZ74lq`。
- **原文定位：** `Make a documentation-only follow-up to the O6 Registry draft and test plan.`
- **原因：** 无法确认 A 看过的计划快照时，不能把当前修订稿冒充原批准版本。
- **F 的指令：** 核查已保存快照；无法核实则报告来源局限，给新稿独立修订号，保留首批范围。
- **可观察结果：** 后续明确原批准快照无法逐字节核实，记录现有证据及修订号 v0.1-DRAFT-r2，未从记忆重建。
- **结果定位：** 同一原生导出内搜索 `The snapshot Role A reviewed could not be verified`。

## F-O6-03：按合并需求纠正 Unknown 显示

- **干预位置：** [20261122_session_transcripts_CS5351_O6.md，用户回合](CS5351_O6.json#L34154)；消息 ID `msg_1f3c08669001tkQ2FrZgLNq59x`。
- **原文定位：** `Task: Prepare the minimal O6 unknown-token display correction plans`
- **原因：** 缺失 token 不能当成 0，也不能让旧测试期望替代需求。
- **F 的指令：** 要求最小计划修正、保留显式零和 partial，不扩大 legacy footer 修改范围。
- **可观察结果：** 后续形成 Unknown 修正计划及四个 token 状态组合/既有披露回归映射；本会话此段为计划证据，不等于已实施。

## F-DEMO-01：纠正被排除测试的归因

- **干预位置：** [20261122_session_transcripts_O6_batch1.md，用户回合](O6_batch1.json#L72394)；消息 ID `msg_1f89b14d0001SAgwoj3mVcE76K`。
- **原文定位：** `Correct the O6 acceptance evidence only.`
- **原因：** 原报告把 integration deselection 误归到 O5 离线测试。
- **F 的指令：** 只核对已有执行/收集记录，找出确切节点，禁止为报告更正重跑全套。
- **可观察结果：** 后续记录被排除的是 DeepSeek live integration 节点；1842 passed 等原数字保留，明确没有 O6 用例被排除。
- **结果定位：** 同一原生导出内搜索 `**Counts preserved:**`。

## F-DEMO-02：让录屏命令真正显示结果

- **干预位置：** [20261122_session_transcripts_O6_batch1.md，用户回合](O6_batch1.json#L76477)；消息 ID `msg_1fec3b78a0017djTbCDxaF3pbd`。
- **原文定位：** `Finish one bounded correction to the three O6 handoff documents just generated.`
- **原因：** pytest 的输出被 harness 截获，仅加 -s 并不能展示承诺的表格。
- **F 的指令：** 要求复用既有 fixture/renderer 的临时可复制演示，不改生产代码，不混入其他输出。
- **可观察结果：** 后续生成可显示输出的临时演示；这一步随后仍需下一条干预纠正常量重建与网络保护，不能视为最终演示已完全正确。
- **结果定位：** 同一原生导出内搜索 `Correction complete.`。

## F-DEMO-03：只展示真实捕获输出并落实离线保护

- **干预位置：** [20261122_session_transcripts_O6_batch1.md，用户回合](O6_batch1.json#L78531)；消息 ID `msg_1fed3e0bd001LBAE4RtnSyBHe4`。
- **原文定位：** `Make two small corrections to the temporary O6 demo and its instructions:`
- **原因：** 重建表格或打印披露常量不等于捕获真实 renderer；仓库外脚本不自动继承 conftest。
- **F 的指令：** 打印 captured["summary_text"] 并断言披露，显式启用网络阻断；只验证一次。
- **可观察结果：** 后续记录真实捕获输出、网络阻断及 1 passed；适用基线 918f6c2，不能当作后来冻结 main 的验证。
- **结果定位：** 同一原生导出内搜索 `**Prints the captured renderer output**`。

## 提交前由 F 确认

- 确认上述干预解释符合本人真实意图；若只是在转达 A/B/C 的决定，保留原决定者身份。
- 不以这些阶段报告的旧 SHA 和测试数量代表最终冻结 main。
