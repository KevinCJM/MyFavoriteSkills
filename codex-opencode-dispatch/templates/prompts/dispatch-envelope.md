# File-based dispatch envelope (not a canonical brief)

Use only after verifying the files are accessible on the OpenCode server. This envelope
is sent as the MCP `prompt` string; it is not a new `prompt_file` API parameter.

```text
Task <ID>, contract <revision>, attempt <attempt>, role <role>.
Work only in <absolute server workspace>; expect snapshot <identity>.
Read <absolute worker-rules copy> first, then <absolute authoritative task brief>.
Those files contain the four-question change gate and exact requirements/admitted changes.
Do not infer authority from chat history or treat an allowed path as permission for cleanup.
If either file, identity, permission or dependency differs, stop and report the mismatch.
Return a compact identity/status/evidence receipt; write detailed output only to the
artifact location authorized by the brief. Do not merely acknowledge; perform the task.
```

Do not repeat acceptance numbers or paraphrase interfaces in this envelope; the brief is
their source of truth. Copy or inline required context when a referenced path is inaccessible.
A file hash can identify a copied brief, but does not prove the worker read or obeyed it.
