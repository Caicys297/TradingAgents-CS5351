# Team covenant for AI-assisted coding

AI suggestions are drafts. The six students own requirements, architecture choices, test plans, approvals, implementation review, and acceptance. A scoped agent plan must be approved before code work; human review and CI follow it. The agent must not self-approve, rewrite prior approval history, edit governance rules as part of a feature task, or merge its own PR.

Keep abstractions limited to the approved architectural element and avoid speculative frameworks or new dependencies. Do not make a test pass by copying the implementation into its oracle. Every new feature needs at least one meaningful negative test. A safety-critical code change needs a recorded architecture decision and human approval before editing. When requirements change, review these rules and update them within the same sprint, with the new version and reviewer recorded.

Use `docs/req/requirements.yaml` for selected requirements and `docs/code-governance/` for module, verification, and tool rules. C's architecture handoff is included under `docs/architecture/` in this branch; check its baseline and any later changes before using it. If documents disagree with the current code or with each other, flag the conflict and ask the responsible human. Keep failure evidence and rejected options; do not turn a later clarification into a claimed earlier approval.
