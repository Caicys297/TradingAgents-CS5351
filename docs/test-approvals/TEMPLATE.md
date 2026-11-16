# Pre-code approval record — TEMPLATE ONLY

Copy one record for each O1–O6 feature or separately approved implementation batch. Fill it from real GitHub comments and actual times. Blank fields are not approval.

| Field | Actual record |
|---|---|
| Feature / owner | |
| Requirements registry commit SHA | |
| Test plan version and immutable GitHub commit link or attached file | |
| Approved requirement IDs and test case IDs | |
| Test scope: fixtures, expected results, negative/boundary cases, offline command | |
| Test reviewer and GitHub approval-comment link | |
| Test approval time with time zone | |
| OpenCode execution plan text/link and version | |
| Execution-plan reviewer and GitHub approval-comment link | |
| Execution-plan approval time with time zone | |
| First implementation-code commit SHA and time | |
| Feature PR link and later code-review/CI links | |

## Recommended sequence

1. Put the versioned test plan in a documentation commit or attach it to the feature's GitHub Issue. Use a commit-specific link or attach the exact file so later edits cannot silently change what was approved.
2. The assigned human reviewer comments **Approved for implementation** with the plan version, requirement IDs, test IDs, allowed files and any exclusions. GitHub records the comment time. A WeChat message can notify the reviewer; preserve an original WeChat message/time if it is the actual approval evidence.
3. Ask OpenCode for an execution plan **without code edits**. Paste the full plan into the same Issue or link an immutable copy. A comments approval of that exact plan and scope before the first code edit.
4. Only then generate implementation code. In the feature PR, link the Issue approval comments, this completed record, the first code commit and CI results. A later PR approval is code review; it cannot retroactively approve a test plan or execution plan.

If the plan changes materially after approval, post the new version and obtain a new approval **before implementing the changed scope**. Do not fill old timestamps from memory or create a retrospective approval.
