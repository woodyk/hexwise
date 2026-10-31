# Hexwise development interaction design

Hexwise centers the developer's work on a protected candidate, its requested behavior and retained evidence. The three columns stay visually aligned: navigation at left, artifact and intent in the center, conversation and version history at right. The composer belongs immediately beneath the artifact so a request remains visibly attached to the bytes it will affect.

## Development lifecycle

| Stage | Developer interaction | Artifact or evidence |
| --- | --- | --- |
| Explore | Browse a local folder, select an existing file or create a starter | Exact original identity and protected copy |
| Specify | Confirm architecture/platform and edit the target contract | Interfaces, dependencies, limits and acceptance criteria |
| Compose | Select a model and ordered feature extensions | Target system prompt plus feature-chain inputs |
| Generate | Send a request against the current candidate | Retained response, checked byte proposal and separate snapshot |
| Inspect | Review hex, byte inspector and changes | Original/current comparison and snapshot ancestry |
| Verify | Preview supported documents or run a matching isolated target | Actual checks with explicit unavailable/not-run states |
| Accept | Review the replacement decision | Backup, unchanged-base check and atomic replacement |
| Collaborate | Inspect Git, commit, push and create a draft PR explicitly | Repository history and review |
| Recover | Restore a snapshot as a new candidate | New ancestry without erasing the existing history |

GUI creation chooses a structural template before composing feature extensions. A layout request such as 4 × 4 becomes concrete rows/columns in both the seed artifact and model context. Chains use the same target prompt at each step, while the candidate and its identity advance. This avoids passing a later extension stale byte offsets.

Manual and AI changes share the same candidate path. A manual edit stays in the buffer until saved; AI requests snapshot a dirty buffer first. Model replies cannot accept changes, replace originals, execute Git actions or launch binaries. Missing target information is part of the conversation, not a reason to guess platform structures.

## Information hierarchy

The editor header identifies the active artifact, size and digest. The active byte row, decoded text and inspector use the same byte offset. Changes are highlighted in amber; the protected original and saved candidates use green. The conversation keeps user intent, assistant proposals and host validation failures distinguishable. Snapshot history supplies the recovery path, and the review card keeps acceptance separate from generation.

Common file actions are available through the menus and command palette. New application, GUI templates, prompt extensions and GitHub remain visible in the explorer footer. Provider and model selection sit beside Send; target profile and attached-byte context sit directly above them. No implementation commands are embedded in the ordinary feature-creation flow.

## Initial release boundaries

The app currently works on one file per protected session. It can propose arbitrary bytes but performs only the validators described in the README. Header recognition is a suggestion, and a successful patch is a serialization result rather than proof of behavioral correctness. Large files need paged context; complete AI replacement is restricted to files fully supplied to the model. GUI starters are HTML documents and use a clearly separate source-based profile.

The next substantial capabilities are multi-file project transactions, instruction-aware diff/disassembly, independent per-target test adapters, signed model/tool provenance, OS keychain-backed persistent credentials, streaming with recoverable task state, and macOS/Windows VM runners. Full compiler/linker integration should be explicitly labeled as a packaging path, alongside complete model-emitted executable generation. Remote collaboration needs project-scoped authorization and must not expose the local service.
