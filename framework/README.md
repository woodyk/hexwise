# Hexwise prompting and training framework

Hexwise 0.1 makes direct byte generation a checkable task: a model receives a behavioral contract, returns bytes or a patch, and a separate tool materializes and evaluates the candidate. The initial implementation handles a small ARM64 function profile so the protocol can be exercised before introducing executable containers and application changes.

Concept attribution: **Wadih Frederick Khairallah — 2b0n2b!!!**. Framework draft: October 29, 2026. AI-assisted implementation. This extends the [Hexwise concept](https://github.com/woodyk/concepts-and-proofs/blob/main/concepts/direct-binary-software/CONCEPT.md) and [development method](https://github.com/woodyk/concepts-and-proofs/blob/main/concepts/direct-binary-software/METHOD.md). The original attribution and provenance remain with those records.

## Name and representation

Keep **Hexwise** as the working name. It describes the external byte representation and keeps the concept's existing identity. Bitwise could describe a broader family of binary reasoning methods, but changing the name does not improve model behavior. This is a naming recommendation, not a trademark or availability check.

Hex offers a compact, inspectable notation relative to spelling every bit: each byte uses two hexadecimal characters instead of eight binary digits. Character count does not establish model token count, accuracy or cost. Compare contiguous hex, spaced hex bytes, byte tokens and instruction-aware encodings using the same tasks and actual tokenizers. Hex is the initial transport; machine bytes are the artifact. Keep representation replaceable beneath a stable behavioral contract.

## Implemented first slice

The target profile `aarch64-leaf-u64-add-v1` accepts raw little-endian A64 instructions. The function receives an unsigned 64-bit value in X0 and returns that value plus a specified constant, modulo 2^64. It uses no memory or external calls. Only unshifted `ADD X0,X0,#imm12` instructions followed by `RET X30` are supported by the smoke interpreter. All other registers, flags and stack remain unchanged. The caller supplies a valid return address.

CREATE writes a new function payload. UPDATE replaces whole instructions in an exact hashed base without changing its length. READ and DELETE remain protocol design work; there is no claim of application CRUD in this implementation. Raw functions require a future harness or packager to become loadable software. The included Python tool never executes generated machine code on the host.

## Run the examples

From this folder, using Python 3.9 or newer:

```sh
python3 -m unittest discover -s tests -v
python3 hexwise.py examples/create.task.json examples/create.candidate.json --out runs/create
python3 hexwise.py examples/update.task.json examples/update.candidate.json --base runs/create/candidate.bin --out runs/update
```

Use a fresh output directory on each attempt. Each run saves the task, candidate manifest, bytes, evaluator report and, for an update, the original bytes. The original input remains intact. Invalid contracts or patch preconditions return exit code 2 before a run directory is created. Structurally accepted candidates with failing or unsupported behavior are retained and return 1. Passing smoke cases returns 0. Existing output directories are refused.

The examples create `x + 1` and change it to `x + 2`. They are authored fixtures, not results from a trained model. The public interpreter evaluates eleven boundary inputs. Its pass means only that these cases passed under its restricted semantics; native execution, independent ISA emulation and executable loading remain separate gates.

The initial validation passed 12 protocol tests and both sets of eleven smoke cases. Apple's Clang assembler independently produced matching bytes for the two authored instruction sequences; it was used for this fixture check, outside the materialization path. `validation.json` records those results and the assembler version. The fixture instructions follow the [Arm A64 reference](https://developer.arm.com/documentation/ddi0602/) and the interface uses a restricted subset of [AAPCS64](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst).

## Use with an existing model

Give the model `PROMPT.txt`, the exact task JSON, and its canonical digest:

```sh
python3 hexwise.py examples/create.task.json --task-hash
```

For updates, also provide the base bytes with their file offsets and observed hash. Save the model's JSON response to a candidate file and run the materializer above. Feed failures back with a fixed attempt and cost budget. Preserve every candidate and report. No provider API, credentials or model installation is needed for this manual workflow.

Start with zero-shot, then compare a few training-only demonstrations and bounded tool feedback. Keep task meaning and acceptance criteria fixed during repair. A model may ask for a corrected contract; the host should route that as clarification rather than trying to decode it as hex.

## Framework files

| File | Purpose |
| --- | --- |
| `PROTOCOL.md` | Trust boundaries, target contract and extension rules |
| `PROMPT.txt` | Reusable model instructions with exact output formats |
| `TRAINING.md` | Record format, curriculum, data splits and evaluation plan |
| `hexwise.py` | Strict task binding, patch checks, writer and smoke interpreter |
| `examples/` | Create/update fixtures and illustrative training records |
| `tests/` | Positive and adversarial protocol checks |
| `prompts/README.md` | Library index for 31 standalone CPU/platform prompts and companion task templates |

The broader prompt library uses the proposed `hexwise/prompt-0.2-draft` response contract. Its profiles are documentation for prompting and future adapters; they do not extend the targets or operations supported by the current CLI. See [the prompt index](prompts/README.md) for selection and use.

## First research milestone

Expand from this wiring check to a family of bounded functions with independent reference behavior and an isolated ARM64 runner. Compare prompted hex, assembly and source/compiler workflows under the same requirements and budgets. Select a representation based on verified behavior per unit of total cost. Only then expand to full executable generation, imports, relocation, unfamiliar application patches and further targets.

The full-executable track should preserve the original ambition: the model supplies every final byte and a generic writer materializes it. A payload-plus-packager track is useful separately; record all compiler, linker, assembler and packager use so results cannot silently conflate the two.
