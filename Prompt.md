# Coding agent task prompt (team draft)

Read the root `AGENTS.md` first. Work on the feature and batch named by the human in this session. Use the current target branch and the approved requirements and test plan for that scope. This is the team's single reusable task prompt; feature details belong in the approved documents and the human's task message.

## Plan first

Inspect the repository without editing files. If the task owner has authorized a read-only check or offline probe, such as pytest collection or callback delivery, you may run it and record the command and result. A probe does not approve code edits. Return a short execution plan that includes:

1. Current branch and commit SHA; requirement IDs, test plan version, case IDs, and link to the designated test reviewer's approval of that exact test plan and scope. Mark any missing approval or document as pending.
2. The actual functions and files to change, what each change will do, and which files stay outside scope.
3. Interfaces and shared files involved, their owners, and any conflict with another feature or the current code. State assumptions and unresolved decisions.
4. The test cases to add or update, with expected results for normal, boundary, and failure paths; the offline and regression commands to run after implementation.
5. A small implementation order and the evidence to retain for the PR and agent transcript.

Stop after the plan. Ask A to approve this exact execution plan and file scope before creating or changing production code, test code, or project configuration. Both the designated test reviewer's approval and A's execution-plan approval must be recorded before the first code edit. If the approved test plan or interface decision is missing, identify what is needed without treating a draft or later PR review as pre-code approval.

## After recorded approval

Follow only the approved plan and file scope. If a material change to requirements, tests, interfaces, or files becomes necessary, stop and request approval of the revised scope before making that change. Keep changes reviewable and link them to the requirement and case IDs.

Run only the approved verification commands. Report the commands and actual results, including failures or checks you could not run. Prepare the implementation PR with links to the pre-code approvals, first code commit, test results, and redacted agent-session evidence. Do not claim that unrun checks passed or that a draft plan was approved.
