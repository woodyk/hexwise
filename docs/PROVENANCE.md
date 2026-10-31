# Origins and provenance

**Wadih Frederick Khairallah — 2b0n2b!!!**  
Repository preparation: October 31, 2026. Implementation and synthesis are AI-assisted.

## Concept lineage

The following project-relevant discussions and records informed this repository:

1. **STRIP and WADIH code.** Selected user messages in the earlier archive describe compact programs, natural-language software creation, iterative modification, execution, GUI output and package delivery. The retained messages are dated November 2023 by their stored timestamps. They are precursors to the interaction model, not evidence that a hex-generating model existed then.
2. **Direct-byte creation and modification, October 2026.** The user proposed machine-code bytes represented as hex as an AI-facing generation/editing interface. The Byte Picture demonstration constructed a bounded graphical ARM64 macOS executable using encoded instructions and identified build tools.
3. **Hexwise concept consolidation.** The related discussion titled “Assess hex editing limits” includes the user's direction to develop Hexwise as a future method with application-level CRUD and new software starting from a touched file. Reusable model-context prompts and a transaction lifecycle were added to the concept record.
4. **Prompting, training framework and Studio design.** The discussion titled “Hexwise model training guide” extends that direction with architecture/platform profiles, checked tasks, provider-agnostic model use, the three-column console, snapshots, feature/layout chains, prompt management and GitHub integration.

This document summarizes the technical direction. It deliberately omits unrelated messages and personal account/security material from those discussions.

## Public source records

- [Original Hexwise concept](https://github.com/woodyk/concepts-and-proofs/blob/main/concepts/direct-binary-software/CONCEPT.md)
- [Development method](https://github.com/woodyk/concepts-and-proofs/blob/main/concepts/direct-binary-software/METHOD.md)
- [Reusable LLM context](https://github.com/woodyk/concepts-and-proofs/blob/main/concepts/direct-binary-software/LLM_CONTEXT_PROMPT.md)
- [Selected STRIP/WADIH transcript references](https://github.com/woodyk/concepts-and-proofs/blob/main/concepts/direct-binary-software/evidence/TRANSCRIPT_REFERENCES.md)
- [Hexwise consolidation record](https://github.com/woodyk/concepts-and-proofs/blob/main/concepts/direct-binary-software/evidence/HEXWISE_CONSOLIDATION.md)
- [Byte Picture proof and limitations](https://github.com/woodyk/concepts-and-proofs/tree/main/concepts/direct-binary-software/proofs/byte-picture)
- [Framework and prompt-library merge](https://github.com/woodyk/concepts-and-proofs/commit/856e688d4abd4cb78aff0b4c62aa4c78da0a5993)

The original concept repository remains the source of the archived proof, source excerpts and its attribution registry. This standalone repository packages the current Studio sources and the earlier framework for continued development. The original Byte Picture binary is linked rather than relabelled as a new model-generation result.

## Evidence boundaries

The framework examples are authored fixtures. Their retained `.bin` files are tiny raw ARM64 payloads used as records; the test interpreter does not launch them. Studio's live model edit checks were bounded byte changes. Its GUI starters are HTML source documents. The Studio application itself uses Python, JavaScript and Swift.

No model training, general autonomous executable synthesis, universal binary CRUD or benchmarked superiority is established by assembling this repository.

## Integrity inventory

`SHA256SUMS` inventories the publication's files. `python3 tools/integrity.py --check` detects missing, changed or newly unregistered files and mismatched copies of the prompt library. Maintainers intentionally regenerate it with `--update` when publishing changes. Git history and provenance retain the change record.

Hashes and visible attribution support tracking; they are not signatures or an independently authenticated priority claim. Third-party libraries, specifications and services retain their own provenance.
