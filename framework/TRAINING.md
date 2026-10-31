# Hexwise training and evaluation plan

Use one behavioral contract and candidate protocol for prompting and training. Training changes how the generator learns to satisfy the contract; it does not replace independent evaluation. The immediate research unit is a verified function or behavior change.

## Curriculum

| Stage | Generator task | Required evaluator |
| --- | --- | --- |
| 0 | Predict effects of bounded instruction bytes | Independent ISA model and edge cases |
| 1 | Create pure integer functions from requirements | Input/output oracle, instruction limits, ABI checks |
| 2 | Patch functions while preserving interfaces | Exact base checks, new behavior and regression suites |
| 3 | Read unfamiliar functions and localize a change | Location-linked claims checked against behavior |
| 4 | Emit complete tiny executables | Container validation, isolated loading, process I/O tests |
| 5 | Extend and remove features in small applications | Feature absence/presence, regression and recovery tests |

The supplied implementation is a stage 1/2 protocol smoke test limited to addition. It is too narrow to establish useful learning or generalization. A suitable next corpus includes comparison, bit masks, shifts, bounded branches, multiargument arithmetic and bounded buffers, each with precise signedness, overflow and memory contracts. Expand the runner before expanding permitted instructions.

## Record format

Keep a provider-neutral JSONL archive. Each record should have:

- `record_id`, task and protocol version, target profile and exact task digest.
- `family_id`, originating project/build lineage and split assignment.
- `generator_input` containing only information available at inference time.
- `candidate` using the exact production protocol.
- `artifact_sha256`, base identity and parent record when applicable.
- `evaluation` with evaluator version, suite identity/digest, environment, individual gate results and failure evidence.
- `provenance` with license/permissions, reference origin, generation tools and whether an assembler/compiler/packager was used.
- Model ID/version, prompt digest, decoding settings, tool interactions, token usage, latency, attempts and cost when applicable.

The illustrative JSONL file contains two authored fixtures with actual smoke evaluation evidence. It is a record-format demonstration, not a training corpus. Missing experiment metadata is null rather than invented. Hash and freeze actual future suite definitions; do not label these public cases hidden.

Build a separate training export from the archive: prompt plus task and authorized observations become input, and only eligible accepted candidates become supervised output. Keep evaluator metadata outside inference inputs. Do not fine-tune on explanations or claims of success as a substitute for the bytes. Do not include the target bytes in a CREATE input; an UPDATE input legitimately includes its exact base bytes.

## Generate reliable examples

Generate reference behavior independently from candidate implementations. Source compilers and assemblers can create training fixtures; label those origins. Build variants can teach equivalent instruction layouts, optimization choices and patch locality. Include incorrect candidates with concrete failure reports for repair training and verified preference pairs. Store failures separately from accepted supervised outputs.

Use checked bit-vector semantics for arithmetic and independent boundary/randomized cases. For richer instructions, compare a pinned emulator with a native isolated runner on sampled cases. Preserve ABI state and guard memory. A shared error in a custom interpreter and fixture builder can create false success; the tiny included interpreter requires external cross-checking before it becomes research evidence.

## Prevent leakage

Assign splits before producing builds or variants. Group by originating project, algorithm family, template and ancestry; compiler flags, symbol stripping, randomized addresses, encoding variations and paraphrases stay with their parent. Avoid assigning add-one to training and add-two to evaluation as a generalization claim. Hold out algorithm families and unfamiliar codebases, and audit byte/normalized-disassembly similarity across splits. Keep private tests and reference outputs outside generator access. Keep final evaluation tasks out of repair and preference data.

## Compare prompting and training

Begin with the same frozen tasks for zero-shot prompting, few-shot prompting and bounded feedback. Add supervised fine-tuning only after there is a diverse verified corpus. Use the same total attempt, tool, latency and cost budgets for every workflow. A source/compiler baseline and an assembly/assembler baseline receive equivalent contracts and tests; record their build overhead. Full-binary and payload-plus-packager results belong in separate comparisons.

For representation experiments, decode every arm to identical byte semantics. Test contiguous hex, spaced hex, instruction-grouped hex and a true 256-byte vocabulary where model tooling supports it. Byte vocabulary changes require tokenizer/model support; relabeling text strings as byte tokens does not supply that support. Record actual token counts, invalid-output rate, correctness, feedback iterations and total cost. Hex suitability for current models remains a hypothesis until measured.

## Acceptance and scoring

Report first-attempt success and success within a fixed repair budget over all tasks, including malformed output and unsupported targets. Preserve separate denominators for valid format, valid structure, behavior, ABI/memory safety and regressions. For updates, evaluate new behavior and explicitly retained behavior separately. A candidate qualifies only when every required gate passes; unavailable required checks prevent qualification.

Measure latency, total tokens/tool calls, cost per qualified change, artifact size and runtime after correctness. Compare equivalent workloads with uncertainty intervals over task families. The current smoke tool produces case results, not those aggregate research claims.

If using execution feedback for preference learning or reinforcement learning, make evaluator-owned correctness the first gate. Penalize malformed output, crashes, timeouts, memory/ABI violations and regressions. Apply size or speed preferences only among fully qualifying candidates. Exact byte matching can check a serialization exercise, but multiple byte sequences can implement the same behavior; it is not the semantic objective.

## Next deliverable

Build an isolated ARM64 runner with randomized register sentinels, protected memory, deterministic resource limits and an independent behavior oracle. Then collect a small pilot across several function families and publish all failure categories. Use its results to choose prompt revisions, representations and whether training is justified before committing to a large corpus.
