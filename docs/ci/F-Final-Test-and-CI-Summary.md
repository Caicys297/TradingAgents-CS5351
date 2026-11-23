# 最终测试与 CI 汇总

整理：F（Chenxi Fan）｜日期：2026-11-22

提交说明（2026-11-23）：本交付基于 main@`2eb77a4188954f5f671f924dbebca7294738c13f`，新增 F 原生会话与汇总。下文测试数字仍绑定其各自历史 SHA，不将 252fe31 的 CI 结果移作新 main 的结果。

本文汇总已有的 O6 测试、跨模块回归、六门禁 CI 和分支保护验证证据，供最终报告及工程交接引用。本次整理未重新运行测试或修改代码、工作流、审批记录及保护设置。测试结果按实际提交版本分别列出，不合并计算不同版本的通过数量。

**交接结论：**六类门禁已实现；#37 的真实事前审批记录经迁移规则验证后通过，#37/#38 均已合并。受控试验 #41 完成缺审查阻断、审批后恢复、失败检查阻断、修复后恢复，最终关闭、未合并。A 已确认六门禁验证结论可供最终报告引用。E3 未执行，O5 S6 已终止、未并入交付；最终工程范围按已合并的 S1–S5 准备。

**main 版本执行证据补充：**已核对 `main@252fe31` 的历史 push CI `44988759013`：15 项成功、2 项 PR-only 跳过。Python 3.11 job 的实际日志为 **2126 passed、1 skipped、1 deselected、100 subtests passed**，其中 O6 三文件共 **36 个用例 PASSED**。这些结果对应已核实的 main 提交，不表示 A 已将该 SHA 确定为最终冻结版本。

## 1. 版本与结果的适用范围

| 证据阶段 | 固定版本 | 可以支持的结论 |
| --- | --- | --- |
| O6 main 集成验证（11-20） | `99612ca64445ec650b9a5f42203fa166783800b1` | O6 36 项、CLI/报告兼容性、该版本默认全量回归结果 |
| CI Closure v5 初始实现 | `9b3ffa282df8e4abd3a531c19b452d990b6be36b` | 定向 47 项、该阶段全量回归 2090 项及当时审批红灯 |
| #37 权限补正与负例证据 | `3314d526df4903dc13220bffad8f5ed91c3acdc0` | 权限测试 21 项；三类真实契约破坏实验的归档证据 |
| #37 审批闭合 | `1c0b7402269db84f9a86892dc94c72a2709360a5` | 两类原始审批通过验证；合并前 CI 17/17 成功 |
| #37 合并后的历史 main push | `6b0b840fc99be4fd87054b7f45739c94a31ee8f9` | 此提交的 push CI：15 成功，2 项 PR-only 检查跳过 |
| #41 恢复后的试验提交 | `9462d6c1ce6a311bd3e334c40572dc9cb176913a` | 试验 CI 17/17 成功；同 SHA 有效审批后恢复可合并资格 |
| 最终交接报告记录的 main；其历史 CI 已联网核对 | `252fe311d8d1483b5713de69b04ce2769c33f1dd` | push run `44988759013`：15 成功、2 PR-only 跳过；Python 3.11 为 2126 passed/1 skipped/1 deselected/100 subtests；O6 36 项 PASSED |

**最终打包基线尚待确认：**`252fe31` 已有真实 main CI 证据，仍以 A 最终冻结的 SHA、对应 CI run 及打包记录为准。若冻结 SHA 相同，可直接引用该次 CI；若不同，按对应版本的实际证据核对，不将历史或试验分支结果移作冻结版结果。

### main@252fe31 的 CI 与逐节点证据

| 核对项 | 实际记录 |
| --- | --- |
| CI run | [44988759013](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013)，`event=push`、`head_branch=main`、`head_sha=252fe311d8d1483b5713de69b04ce2769c33f1dd` |
| 工作流结果 | 四个 Python 回归环境及其余适用检查共 15 项 SUCCESS；`test approval`、`ai-use log` 按 PR-only 条件 SKIPPED，无失败 |
| Python 3.11 详细日志 | [job 137104997890](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013/job/137104997890)：2126 passed、1 skipped、1 deselected、100 subtests passed |
| O6 用例 | 处理器 13、子图 5、CLI 18，共 36 个用例均有 PASSED 行，属于上述 2126 项之内 |
| #43 矩阵引用复核 | 固定 `11828d6f98ec6e62977f8a0ebfea7375158f2709` 的 166 个不同测试函数引用，在该 job 均有对应 PASSED 记录；函数引用数不等于参数化执行例数 |

这是读取既有执行日志得到的证据，不是本次重新运行测试。Python 3.11 的精确数量不套用于其他三个环境；逐节点通过也不自动证明 97 条需求的全部验收标准已满足。main push 的两个跳过不替代 #37 PR 中真实审批和 AI-use 检查成功的证据。

## 2. 测试入口与离线边界

仓库要求 Python ≥3.11。O6 main 验证实际环境为 Python 3.12.15、pytest 9.2.0、langchain-core 1.8.4。下列命令用于定位和复现既有验证，不表示在本次文档整理时已执行。

```bash
python -m pip install -e ".[dev]"

# O6：统计处理、真实子图身份绑定、CLI 接线与显示
python -m pytest -q test/offline/test_o6_per_analyst_stats.py test/offline/test_o6_analyst_subgraph.py test/offline/test_o6_cli_wiring.py

# CLI 兼容性
python -m pytest -q tests/test_cli_display.py tests/test_cli_headless.py tests/test_cli_no_console.py tests/test_cli_config_precedence.py

# 报告、HTML 和评级兼容性（与上一组存在重叠，不累加计数）
python -m pytest -q tests/test_reporting.py tests/test_report_html.py tests/test_rating_integrity.py tests/test_cli_display.py

# 默认回归与静态检查
python -m pytest -q
python -m ruff check .

# 权限专项与需求注册表
python -m pytest -q test/offline/test_permissions_guard.py
python scripts/validate_requirements.py
```

默认 pytest 搜索 `tests/` 和 `test/offline/`，配置为 `-m "not integration"`；因此默认回归不等于外部服务联调。`test/offline/conftest.py` 对非 integration 测试禁止 socket、DNS 和 curl_cffi 请求，意外联网会失败。该目录的 fixture 不会自动作用于仓库外临时演示脚本。

在 `99612ca` 的全量验证中：

- 1 项跳过：Bedrock 可选依赖 `langchain_aws` 未安装。
- 1 项排除：`tests/test_deepseek_reasoning.py::TestDeepSeekLiveStructuredOutput::test_v4_flash_returns_structured_output`，需要真实服务并带 integration 标记。
- O6 测试没有跳过或排除；O5 离线文件 `test/offline/test_o5_macro_news_integration.py` 未因文件名含 integration 而被排除。

以上跳过和排除数量只属于该次运行，不能直接套用于后续版本。配置来源：[pyproject.toml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/pyproject.toml)、[离线网络保护](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/test/offline/conftest.py)。

## 3. O6 功能与回归结果

以下保留 main@`99612ca` 的历史专项实测记录。较新的 main@`252fe31` 详细 CI 已另外确认相同三个 O6 文件的 36 个执行用例全部 PASSED，见第 1 节；两个版本的结果不累加。

| 验证范围 | 实际结果 | 说明 |
| --- | --- | --- |
| 统计处理 `test_o6_per_analyst_stats.py` | 13 passed | 计数、tokens、耗时、去重、归属及兼容接口 |
| 子图身份绑定 `test_o6_analyst_subgraph.py` | 5 passed | ordinary/wrap_up、交错执行、越界调用排除 |
| CLI 接线 `test_o6_cli_wiring.py` | 18 passed | 单次注册、显示、顺序、隔离、披露和 footer |
| 三个 O6 文件合并运行 | 36 passed，无跳过 | 与前三行是同一集合，不重复计数 |
| CLI 兼容性组 | 64 passed | 显示、headless、无 console、配置优先级 |
| 报告/HTML/评级兼容性组 | 107 passed | 与 CLI 兼容性组有交集 |
| 默认全量回归 | 1842 passed，1 skipped，1 deselected；100 subtests passed | 不将 subtests 当作额外独立测试累加 |
| 全仓 Ruff | 通过 | 该版本静态检查结果 |

### 需求对应的主要证据

| 需求 | 主要验证点 | 代表测试 |
| --- | --- | --- |
| O6-FR-01 | 仅归属到已选且身份验证通过的 Analyst；统计调用、tokens、耗时；普通调用和 wrap_up 均归属 | TC-O6-01、07、13；子图测试 |
| O6-FR-01 | 缺失/无效身份进入 unattributed；非 analyst scope 不进入命名行或 unattributed | TC-O6-08、10、10b、11；W-8b、W-12 |
| O6-FR-02 | 输入/输出完整性独立；Unknown、显式 0、partial 小计区分 | TC-O6-02、03；W-9、W-10 及五项显示用例 |
| O6-NFR-01 | 交错及逆序完成、运行隔离、run_id 重放去重 | TC-O6-04、05、06、07b、14 |
| O6-NFR-02 | 旧 `get_stats()` 四字段保留；离线可重复验证 | TC-O6-09；离线测试保护 |
| CLI 接线与披露 | 单 handler、规范行序、两项披露、普通路径和 checkpoint footer | TC-O6-12；W-1、2、5、7、15a、15b |

W-13 的 `update_display` 未变结论来自源代码/哈希比较，**不是运行时测试**。子图与 CLI 测试使用离线模型和供应商替身；不将其描述为真实供应商联调。测试定位：[O6 测试目录](https://github.com/Caicys297/TradingAgents-CS5351/tree/99612ca64445ec650b9a5f42203fa166783800b1/test/offline)。

另有固定 `918f6c2` 的离线显示演示：真实 renderer 的捕获文本显示 Market 2 次、输入 180、输出 35；News 1 次、输入 80、输出 15；unattributed 为 0，并打印两项披露。该演示不是交互式离线 CLI，也不打印 W15 footer；耗时显示 0.0s 不能作为性能测量。

## 4. 六类门禁与 17 个检查

“六类门禁”是需求分类；“17 个检查”是 CI 上实际出现的检查名称。Contract/Security/API/Permissions 是静态治理子项，不另算四类原始门禁。

| 原始门禁 | CI 检查名称 | 实现及验证范围 |
| --- | --- | --- |
| Test Approval | `test approval` | PR-only；验证 test-plan、execution-plan 的真实事前审批、角色、版本与范围绑定 |
| Static Analysis | `ruff (strict, full repo)`；`type check`；`dependency audit`；`governance contract`；`governance security`；`governance api`；`governance permissions` | 最终树与提交范围检查；治理检查按受保护路径和映射节点触发 |
| Requirements Schema | `requirements schema` | 注册表 schema 校验；E2/E5 中观察到失败和恢复 |
| Semantic Evaluation | `semantic (deterministic O5)`；`semantic (deterministic O4)` | 确定性离线用例；O4 为批准的六个代表节点 |
| Regression | `tests (py3.11)`；`tests (py3.12, America/New_York)`；`tests (py3.13)`；`tests (py3.14)`；`clean-install smoke` | 四环境回归与不安装 dev extras 的安装/导入验证 |
| AI-use Log | `ai-use log` | PR-only；校验新增使用记录与证据结构，不独立判断记录真实性 |

固定版本实现：[CI 工作流](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)。正常 PR 具有上述 17 项；main push 中 `test approval` 和 `ai-use log` 按条件跳过，不能把跳过写成通过。

### CI 实现、审批闭合与真实负例

- #37 初始实现阶段 `9b3ffa2`：定向集合 47 passed，其中 O4 六节点 6 passed；全量回归 2090 passed、1 skipped、1 deselected。两者包含关系及不同运行结果不累加。
- 权限补正阶段 `3314d52`：权限测试 21 passed，专项 Ruff 通过；覆盖 secrets 点号/下标引用、权限字典逐值校验、未知或表达式值失败关闭，以及 PR checkout 不保留凭证。此阶段没有为文档补证重复运行全量回归。
- #38 授权迁移合并后，#37 同步 main，使用 #35 固定计划 `ed0589f0041444e72e2b87d6ba0eb4e12858f59e` 和 A 的原始审批来源完成验证。记录分类调整为 CI，未改写原审批时间、计划 SHA 或批准范围，未复用 #38 的批次例外。
- #37 最终 HEAD `1c0b740`：[CI run 44979161445](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44979161445) 全 17 项成功，包括 Test Approval；随后合并为 `6b0b840`。
- `6b0b840` 的历史 [main push run 44979975741](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44979975741) 为 15 成功、2 跳过，无失败。

三类真实负例在隔离临时副本中改坏契约，调用实际映射节点；正式生产文件未保留故障：

| 类别 | 实际映射节点 | 故障与观察 | 退出码 |
| --- | --- | --- | --- |
| Contract | `test_resume_is_fresh_execution_for_gate` | 移除 completion 重置，`g.last_completion is None` 断言失败 | 1 |
| Security | `test_o2_tc_05_artifact_stability_labels_and_relative_paths` | 移除路径越界拒绝，出现 `DID NOT RAISE ValueError` | 1 |
| API | `test_rt4b_ticker_news_signature_unchanged` | 将 `end_date` 改为 `to_date`，签名断言失败 | 1 |

三项对照均通过，变异后均非零退出。独立原始滚屏日志未完整保留；可引用归档的观察和会话证据，不能声称持有完整原始日志。见 [CI-Closure-v5-Evidence.md](https://github.com/Caicys297/TradingAgents-CS5351/blob/3314d526df4903dc13220bffad8f5ed91c3acdc0/docs/ci/CI-Closure-v5-Evidence.md)。

## 5. 分支保护配置与实际阻断

配置证据和行为证据分开使用，不能以 CI 通过替代 required 配置或实际阻断验证。

A 提供的四张截图已收到并归档，显示 main 必须通过 PR、至少 1 个 Approve、新提交使旧审批失效、17 项 required checks（来源 GitHub Actions）、分支保持最新及禁止 bypass（含管理员）；强推和删除未开启。**无独立管理员 API 读回。**F 账号查询 `protected:true`，protection 为 404、rulesets 返回空，不据此推断没有保护。截图本身不提供独立的保存成功或 API 读回证明。

### #41 受控试验

| 项目 | 固定提交 | 实际观察 | 结论 |
| --- | --- | --- | --- |
| E4 缺审查阻断 | `a3d7ec425efb8ccf1372efe3344d8633f2c9892e` | 17 项成功、无 Review；`REVIEW_REQUIRED/BLOCKED` | 通过 |
| E1 审批后恢复 | 同上 | 同 SHA 获 A 真实非作者审批；`APPROVED/CLEAN/MERGEABLE` | 通过 |
| E2 失败检查阻断 | `857e7628345038517e16d9df16962faae23db254` | 同 SHA 已 APPROVED；Schema 与四个关联回归失败，其余 12 项成功；`BLOCKED` | 通过 |
| E5 修复后恢复 | `9462d6c1ce6a311bd3e334c40572dc9cb176913a` | 恢复原值，17 项成功，同 SHA 新有效审批；`APPROVED/CLEAN/MERGEABLE` | 通过 |
| E3 缺失 required 结果 | — | A 排除本次执行 | 未执行 |

E2 的一处可逆 Schema 故障同时触发五项失败，已获 A 明确授权；这证明“已有审批仍被失败检查阻断”，不声称单 job 隔离或逐项验证全部 17 个检查。新提交后旧审批出现 `DISMISSED`，也有实际观察。

E5 恢复文件 SHA256 为 `46753a0a6b46b4edc890c425f807e6f87b627b83b8f5396c789a404e75fd873a`，与故障前一致。恢复通过正常追加提交完成，无强推、历史改写或保护规则修改。[CI #200](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44998474208) 全 17 项成功；同 SHA 审批时间为 2026-11-22T07:43:51Z。关闭前已记录恢复合并资格，随后按指示关闭 #41、未合并。

行为归档：[最终结果评论](https://github.com/Caicys297/TradingAgents-CS5351/pull/41#issuecomment-7076164337)；授权和配置说明见 [#37 讨论](https://github.com/Caicys297/TradingAgents-CS5351/pull/37#issuecomment-7073837395)。四张截图及 SHA256 清单随私发 CI 交接包提供给 A，本文不链接个人电脑绝对路径。

## 6. 交付范围、限制与引用材料

| 项目 | 最终整理口径 |
| --- | --- |
| #37 CI 闭合 | 已合并；真实事前审批经规则验证通过，合并前 17 项成功 |
| #38 授权迁移 | 已合并；缺少本批次机器可验证事前记录的事实和原始红灯保留，A 记录批次特定偏差处置；不能将事后代码审核冒充事前批准，也不适用于 #37 |
| #41 保护验证 | E1/E2/E4/E5 完成，关闭未合并；E3 未执行 |
| O5 S5 | #39/#40 已合并；此前单次 LIMIT_ZERO CLI 探针只支持该分支，不扩大为所有 S5 分支实测 |
| O5 S6 | #33 关闭未合并；记录的最新性能 p95 114.376 ms 超过 100 ms，失败与阈值均保留；历史较快结果不能替代该失败，S6 不列完成 |
| 治理覆盖 | Contract/Security/API 为映射节点验证，不是全仓所有契约及安全属性扫描 |
| 其他未核验边界 | 原交接保留的逐提交 push 语义收口、integration/live 完整入口清单、非确定性语义评分及阈值、安全路径 ADR 强制，本文不新增“已完成”结论 |
| 最终冻结版本 | main@252fe31 已有真实 CI 和逐节点日志；待 A 确认最终冻结 SHA 后绑定打包记录，不挪用其他版本结果 |

### 采用的已有材料

以下文件是本汇总的材料来源名称，已由 F 本地资料核对；与 GitHub 已发布证据结合引用。材料中的旧“等待合并/迁移/截图”表述按最终交接状态更新，历史测试数字仍绑定原 SHA。

| 来源文件 | 本文用途 |
| --- | --- |
| `2026-11-20_17-55-16_O6_Final_Main_Integration_Verification.md` | O6 需求映射、36 项、兼容性、1842 项回归及排除原因 |
| `2026-11-19_21-58-15_O6_Unknown_Token_Correction_Implementation_Verification.md` | Unknown/0/partial 显示补正的历史依据 |
| `2026-11-21_23-45-12_O6_Offline_Demonstration_Instructions_v1.1_CORRECTED.md` | 离线真实 renderer 演示及可见输出边界 |
| `2026-11-22_011843_CI_Closure_v5_Implementation_Report.md` | 初始 CI 实现、47 项、2090 项及阶段审批红灯 |
| `2026-11-22_024111_PR37_Gapfix_Publication_Report.md` | 权限专项 21 项、三类负例及原始日志限制 |
| `2026-11-22_111249_PR37_Approval_Gate_Closure_Report.md` | #37 同步迁移、原审批绑定及最终 17 项成功 |
| `20261122_155836_Six_Gates_FINAL_Handoff.md` | 六类门禁最终状态、合并状态、S6 和未核验边界 |
| E4 阶段报告及 E1/E2/E5 的 F Readback 记录 | 缺审批/失败阻断、修正恢复及关闭前状态 |
| 截图附录与 `20261122_Protection_Config_Screenshots_SHA256.txt` | 四张管理员截图、17 项名称及完整性校验 |
| main push run `44988759013` 与 Python 3.11 job `137104997890` | 252fe31 的真实执行结果、O6 36 项及 #43 的 166 个函数引用对应 PASSED 记录；相关原始行摘录已归入私发素材 |

相关项目入口：[PR #37](https://github.com/Caicys297/TradingAgents-CS5351/pull/37)、[PR #38](https://github.com/Caicys297/TradingAgents-CS5351/pull/38)、[试验 PR #41](https://github.com/Caicys297/TradingAgents-CS5351/pull/41)、[S6 PR #33](https://github.com/Caicys297/TradingAgents-CS5351/pull/33)。F 的会话与干预说明另见[五份原生会话导出（原样提交）](../../transcripts/F/README.md)及[干预位置—原因—结果](../../transcripts/F/F_Intervention_Annotations.md)。
