# Change admission — insert in the authoritative design/brief

For every independent proposed change, answer Q1–Q4 before implementation. Group only
changes with the same justification and contract effect. Reuse this table across dispatch,
report and review; do not duplicate it in every message. Full details:
[change admission](../references/change-admission.md).

| Change / paths | Q1: current requirement / AC | Q2: what fails if unchanged? | Q3: smallest correct intervention | Q4: relevant contract, preservation evidence / unresolved gap | Disposition |
|---|---|---|---|---|---|
| C-1: <specific change> | <user-authorized requirement and AC> | <concrete unmet outcome or necessary check> | <minimal action and bounded effect> | <API/config/log/data/dependency/workflow/compatibility assessment> | eligible / omit / blocked |

Q1 or Q2 fails: omit. Q3 unresolved: narrow the design. Q4 uncertain/conflicting: block
that edit. Codex cannot waive the user's rule. Any explicit user-authorized contract delta
must be recorded as a revised requirement, not quietly introduced as implementation detail.

For a small direct/compact task, do **not** create a C-ID table or ledger merely for ceremony.
One concise `Boundary:` sentence may cover the four questions. Use the full table for
medium/high-risk, contract-sensitive, parallel/dependency-heavy work, or when traceability is
needed for rework. For rework, reference existing rows when they exist and provide only the
changed answers/evidence. A finding is not authority.
