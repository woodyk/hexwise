# Validation and evidence scope

**Wadih Frederick Khairallah — 2b0n2b!!!**  
Public project summary of local checks recorded October 29–31, 2026. No account credentials, private conversations or machine-security audit are included.

| Area | Recorded result | Scope |
| --- | --- | --- |
| Studio Python tests | 51 passing | Storage, exact backups, stale/conflicting edits, integrity, preferences, prompt chains, providers, real local HTTP and local Git integration |
| Framework Python tests | 12 passing | Strict protocol/task binding, patch preconditions, fixture evaluation and failure retention |
| JavaScript | Parse passes; 8 checks pass | Three modal-confirmation regressions, two pane-size constraints and three clarification-render checks |
| ARM64 fixtures | Create and update pass 11 public interpreter cases each | Authored `x + 1` and `x + 2` fixtures under restricted semantics; assembler independently cross-checked the bytes |
| Live model edits | Gemini and local Ollama produced checked candidates | Small exact byte edits; originals retained; not a broad model benchmark |
| Native macOS window | Workspace editing, saving, prompt selection, recovery and quit/close guards verified | arm64/macOS 12+ build, installed Python, local ad-hoc signature |
| GUI starters | Four layouts exercised interactively | 4×4 grid, navigation/filtering, record notes and developer editor/preview |
| Git/GitHub | Local Git and public repository read verified | Local bare-remote push/fetch; remote publication and private PR writes were not part of those original app tests |
| Docker runner | Command/resource controls tested with a simulated process | Live execution was unavailable because the daemon was not running |
| Native Documents read | Unresolved timeout on the development Mac | Existing permission showed enabled. A reauthorization diagnostic was cancelled; the original enabled state was restored. |

A successful hash/patch or basic format check does not establish that a program loads, obeys an ABI or implements its intended behavior. The ARM64 smoke evaluator accepts only its declared instruction subset. No general trained-model result or efficiency benchmark is asserted.

## Reproduce the checks

From the repository root:

```sh
python3 -m unittest discover -s studio/tests -v
python3 -m unittest discover -s framework/tests -v
node --check studio/web/app.js
node studio/tests/test_ui.js
python3 tools/integrity.py --check
```

Python is the only runtime requirement for the local service. Node is used for the JavaScript checks. Local HTTP tests need loopback access, and Git integration tests need Git installed. The tests use temporary fixtures and do not need provider credentials.

Historical framework results are retained in `framework/validation.json` and its authored example runs. The current local audit may be reproduced and extended; CI results should be reported for the actual commit that ran.

The October 31 desktop clarification fix adds coverage for all 31 architecture adapters, an empty macOS ARM64 file, follow-up requirements, prompt-chain stopping and rejection of byte proposals mixed with clarification statuses. These are deterministic adapter and transaction regressions; they do not establish native model-generation capability.
