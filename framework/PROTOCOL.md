# Hexwise candidate protocol

The task is trusted host input; the candidate is an untrusted model proposal. The host owns target selection, base identity, test authority, resource limits and promotion. The model proposes implementation bytes. Success is a verified behavior change tied to exact artifact identities.

## Target contract

Version 0.1 uses a named fixed profile to avoid ambiguous combinations of ISA, ABI and runtime. `aarch64-leaf-u64-add-v1` means A64, little-endian instruction bytes, an AAPCS64-compatible leaf-function interface restricted to X0 input/output, and no OS or executable container. Entry offset is zero. There are no imports, relocations, stack accesses, memory accesses or processor extensions. Only the instructions listed in README are accepted by the interpreter. The profile is deliberately smaller than general AAPCS64.

For future executable profiles, require ISA revision/features, endianness, OS/version range, executable format, ABI/calling convention, entry point, imports/runtime interfaces, dependency versions, memory layout, resource limits, loader and signing policy. Reject missing fields. Inspect existing artifacts to verify the declared target before editing. A profile name must never silently change meaning.

## Task fields

The exact required fields are `protocol`, `task_id`, `operation`, `target_profile`, `requirement`, `addend`, `base_sha256` and `max_bytes`. See the example JSON files. Unknown fields are rejected. `addend` is an unsigned integer in [0, 2^64−1]; `max_bytes` is a positive multiple of four between 4 and 4096. CREATE requires a null base identity. UPDATE requires a lowercase SHA-256 digest of the exact original bytes. The trusted task author must reconcile prose with addend before dispatch; the model should flag contradictions.

For cross-language implementations, preserve integers exactly, including values above 2^53−1. Canonical task serialization is UTF-8 JSON with sorted keys, no whitespace, ASCII escaping, and integer decimal notation, as implemented by `canonical()` in `hexwise.py`. SHA-256 over these bytes binds the proposal to all task fields. This local serialization is not a claim of compliance with a general JSON canonicalization standard.

## Candidate fields

Both operations copy protocol, task_id, operation and target_profile and include the tool-supplied task_sha256. CREATE adds `hex`. UPDATE adds an `edits` array of `{offset, before, after}`. Hex must contain nonempty lowercase byte pairs without separators. JSON duplicate keys, unknown keys, invalid types and nonstandard numeric constants are rejected.

Patch offsets are original-file byte offsets, sorted in ascending order. Every range must start and end on a four-byte instruction boundary, stay inside the base, match expected original bytes and preserve length. Overlaps, insertions and deletions are rejected in this revision. All preconditions are checked in memory before output. Result identity comes from the materializer, never from a model's guessed hash.

This limits accidental corruption; it does not prove intended semantics. General insertion, executable restructuring, relocation and code signing require a new profile and corresponding validation. A generic overwrite tool must not imply those capabilities.

## Evidence and lifecycle

```text
trusted task + pinned base
        ↓
model candidate → contract and byte checks → separate candidate artifact
        ↓ rejected                           ↓
retained response                    evaluator evidence
                                             ↓
                                   retain or repair candidate
                                             ↓
                             future explicit promotion gate
```

The current CLI retains structurally accepted runs and their failures. A caller collecting model output should also retain rejected responses, errors, timing and model settings. No deployment or promotion is implemented.

Keep these statuses distinct: contract acceptance, payload structure, behavioral tests, memory/ABI checks, loader validation, signing validation, and promotion. Not applicable, not run and unsupported are different from pass. The smoke report explicitly names its interpreter and claim scope. A digest proves identity, not safety or behavior.

The next runner should accept a candidate digest and evaluator-owned suite ID and return structured evidence with runner/environment identity, timeout/resource results, test outcomes and ABI observations. Hidden inputs and expected outputs stay outside generator context. Never let candidates supply shell commands, executable paths or their own evaluator. Native candidates belong in a disposable VM or suitable isolated target runner with finite CPU, memory and instruction budgets.

## Read and feature removal extensions

READ should return claims with artifact digest, file offsets, byte ranges, evidence type and confidence. Test inferred behavior independently. UPDATE will eventually support relocating changes and replacement artifacts. DELETE should describe a feature to remove and retained behaviors to preserve; it will generate a new candidate subject to both absence and regression tests. Whole-file deletion and user-data erasure are outside that operation.

For application work, retain container validation, disassembly, acceptance and regression evidence, dependencies and recovery assumptions alongside each version. Promotion must recheck base identity and preserve the working version. Rollback of a binary alone cannot undo external data migrations.
