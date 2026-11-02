# Hexwise application build and prompt evaluation

Run date: November 1, 2026. Concept attribution: **Wadih Frederick Khairallah — 2b0n2b!!!**. AI-assisted test implementation.

The tests demonstrate working bounded application builds, while exposing model and prompt failures. They do **not** establish reliable arbitrary application generation or universal architecture support. Model responses, failed candidates and snapshots are retained in the evaluation folders. Original input files remained unchanged.

## Working builds

- **Counter GUI:** Gemini 3.1 Flash Lite generated the UTF-8 HTML as hex. Two revised/final runs passed real browser checks: initial 0, Increment twice to 2, Decrement to 1, Reset to 0, Decrement to -1, Enter-key activation and aria-live. No evaluator rewrote the generated program. A successful payload was packaged by a separately authored Swift/WebKit shell, compiled, ad-hoc signed, launched as a macOS app and tested again. The packager added a restrictive CSP. This is HTML generation plus a native packager, not native machine-code synthesis of the whole application.
- **Native ARM64:** a model-generated 8-byte ADD/RET payload was constrained by a byte whitelist, packaged through a fixed Clang C/assembly-byte driver, signed and actually executed on Apple Silicon. Each passing candidate matched 41 boundary/random arithmetic cases. Wrong-immediate candidates were refused before execution. No broad ABI or arbitrary instruction claim is made.
- **Complete WebAssembly:** Gemini 3.5 Flash produced a complete 41-byte module. Its first attempt failed validation; its second passed Node's WebAssembly validator and all 70 independent boundary/random addition cases. Imports, start, memories, tables and globals are prohibited. No source compiler produced the module.
- **All four authored GUI starters:** browser interactions verified the 4×4 grid, panel/theme toggles, sidebar navigation/search/settings, master/detail note retention and filtering, and studio editing/preview/document retention. These templates are authored fixtures, separate from live model evidence.

## Full model-task record

Each task had at most two attempts per stage; failures were retained. The initial stage used the old adapter. Later stages explicitly tested corrected instructions, improved error feedback and local context settings. Changing the model or prompt begins a separate stage; the table is not a statistical benchmark.

| Stage | Provider / model | Task | Final result | Attempts |
| --- | --- | --- | --- | --- |
| Baseline | gemini / gemini-3.1-flash-lite | counter | failed | 2 |
| Baseline | gemini / gemini-3.1-flash-lite | wasm-add | failed | 2 |
| Baseline | gemini / gemini-3.1-flash-lite | arm64-add7 | failed | 2 |
| Baseline | ollama / llama3.2:latest | counter | failed | 2 |
| Baseline | ollama / llama3.2:latest | wasm-add | failed | 2 |
| Baseline | ollama / llama3.2:latest | arm64-add7 | failed | 2 |
| -Revised | gemini / gemini-3.1-flash-lite | counter | passed | 1 |
| -Revised | gemini / gemini-3.1-flash-lite | wasm-add | failed | 2 |
| -Revised | gemini / gemini-3.1-flash-lite | arm64-add7 | passed | 1 |
| -Strong | gemini / gemini-3.5-flash | counter | failed | 2 |
| -Strong | gemini / gemini-3.5-flash | wasm-add | passed | 2 |
| -Strong | gemini / gemini-3.5-flash | arm64-add7 | passed | 2 |
| -Ollama-Revised | ollama / llama3.2:latest | counter | failed | 1 |
| -Ollama-Revised | ollama / llama3.2:latest | wasm-add | failed | 1 |
| -Ollama-Revised | ollama / llama3.2:latest | arm64-add7 | failed | 1 |
| -Final | gemini / gemini-3.1-flash-lite | counter | passed | 1 |
| -Final | gemini / gemini-3.1-flash-lite | wasm-add | failed | 2 |
| -Final | gemini / gemini-3.1-flash-lite | arm64-add7 | passed | 1 |

## Failures and corrections

The original adapter allowed ambiguous interpretation of the replacement shape. Models omitted base hashes, encoded HTML in Base64 instead of hex, returned empty artifacts, emitted incorrect ARM64 immediates or malformed WebAssembly. Hash and range checks preserved the originals.

The desktop instructions now give complete examples for every response shape, require the base hash on replacements and analysis, explicitly prohibit Base64, distinguish genuinely missing requirements from an empty but fully specified file, and request a final encoding/budget check. The host now rejects proposals that produce no byte changes, and includes its validation feedback in the next model conversation. Hash checks remain mandatory; missing hashes are never silently supplied by the host.

Ollama requests now specify a 32768-token context and an 8192-token generation ceiling rather than relying on runtime defaults. This can require more memory and does not certify support for every large file context. The tested local llama3.2 model still failed these application-generation tasks, so local-provider connectivity must not be confused with demonstrated model capability.

## Reproduce

From the source repository root, with existing provider credentials in the environment:

```sh
python3 -m unittest discover -s studio/tests -v
python3 -m unittest discover -s framework/tests -v
node studio/tests/test_ui.js
python3 studio/tests/run_live_acceptance.py --out /absolute/fresh/evaluation-directory --provider gemini:YOUR_MODEL --attempts 2
```

The opt-in live evaluator uses fresh disposable files, preserves raw responses and snapshots, and never writes provider keys. It needs Node for WASM and macOS Apple Silicon with Clang/codesign/otool for native execution. A failing task exits 1; an otherwise successful run still awaiting real browser evaluation exits 2. A document is never marked behaviorally correct merely because its source looks plausible.

The UI browser results and packaged-demo check were performed separately through actual controls. Docker execution was not tested because its daemon was unavailable. Windows, iOS, Android, other CPU families, firmware and UEFI builds remain unverified. No release or main-branch merge is implied by these test results.
