# Hexwise vision: software as an editable artifact

**Wadih Frederick Khairallah — 2b0n2b!!!**  
Concept and project direction; AI-assisted synthesis, October 31, 2026.

Hexwise proposes a development method in which a person expresses intent and an AI creates or maintains the artifact that implements it. The model-facing representation begins with hexadecimal bytes. The user-facing experience combines a conversation, an inspectable artifact and evidence that a proposed version does what was requested.

## A touched file as a starting point

The strongest creation goal starts with a new empty file, a behavioral specification and a complete target contract. The model supplies all bytes required for a loadable executable. An empty file provides storage; the model or identified packaging tools must still supply instructions, data, loader metadata, imports and other platform requirements.

Two tracks should remain separately measured:

1. **Complete executable emission:** the model supplies every executable byte and a generic writer materializes them.
2. **Payload plus packager:** the model supplies instruction bytes and metadata; an identified assembler/linker/packager completes the artifact.

Studio's HTML GUI starters form a separate source-based creation path. They provide useful product scaffolding and prompt composition while direct native generation develops.

## A common maintenance interface

Create, Read, Update and Delete describe application behavior. They require binary understanding, target-specific integration and independently evaluated outcomes. Reading can use strings, headers, symbols, disassembly, optional decompilation and runtime observations. Updating may involve local patches, added code/data with repaired references, or a full replacement. Deleting a feature must preserve the behavior that should remain.

Original source-language diversity is one motivation for an artifact-centered method. Access to an executable does not by itself reveal all semantics or confer access to unavailable services, hardware, dependencies or platform credentials.

## Why the ambition matters

A reliable conversational CRUD interface could let developers work at the level of capabilities and verified outcomes across a wider range of artifacts. It could also make exact identity, regression evidence and recovery integral to every software change.

The question is whether specialized models and tools can make that interface sufficiently reliable, understandable and economical to improve real development. The potential revolution lies in that change of interaction and verification, not an intrinsic speed advantage from writing identical instructions as hex.

## Evidence as part of the artifact

Every candidate should retain its requirements, frozen target contract, input/output hashes, parent snapshot, requested change, patch or full replacement, provider/model metadata, independent test results and recovery information. Model explanations alone are not execution evidence.

Evaluate new behavior and preserved behavior. Record failed attempts, unsupported targets and unavailable runners. Compare against AI-generated source/compiler and assembly baselines using the same tasks and budgets. Report generation cost, regression rate, artifact size, runtime, maintenance effort and total cost only after correctness gates pass.

## Expansion toward applications and systems

Progress from instruction semantics and bounded functions to loadable programs, unfamiliar application changes and multi-file projects. Operating-system components belong in later experiments with disposable VMs, boot/regression checks and recovery snapshots.

"Any application" remains the intended breadth across supported targets. Generalization, trainability and economic advantage are open research questions. The current console and bounded proof artifacts are a foundation for investigating them.
