# Hexwise Studio

Hexwise is a local developer console for inspecting bytes, making manual or AI-assisted changes, and retaining every candidate before accepting a replacement. The 0.2 developer release provides a native macOS window around a local Python service and web interface. The same service can run in a browser on macOS, Linux or Windows with Python 3.9 or newer.

Concept attribution: **Wadih Frederick Khairallah — 2b0n2b!!!**. Application design, code and documentation are AI-assisted. This is an initial developer release, not a claim of general model-generated executable correctness.

## Open the application

Build **Hexwise.app** from these sources on an Apple silicon Mac. Native Open File and Open Folder actions use the macOS picker. Python 3.9 or newer must be installed. The app is locally ad-hoc signed, not notarized or packaged with Python. It uses Cocoa and WebKit already provided by macOS.

The source distribution also runs directly:

```sh
python3 server.py --workspace /absolute/path/to/your/workspace
```

This launches the local interface in your browser. No Python packages or frontend build tools are required. `bash launch.sh --workspace /absolute/path` is equivalent. Windows users can use `py -3 server.py --workspace C:\path\to\workspace`.

To preserve API credentials already set in your shell when running the desktop app, launch its executable from that shell:

```sh
/absolute/path/to/Hexwise.app/Contents/MacOS/Hexwise
```

Launching through Finder uses Finder's environment, which may not contain your shell's API credentials. You can also enter a session key under **AI → Provider connections**. Hexwise keeps those keys in process memory; it does not write them into projects or browser storage. No API keys are included in this distribution.

## Workspace layout

The left column browses local folders and files. The center contains the hex editor with its prompt composer directly below. The right column contains Conversation, Snapshots and Prompts tabs. Drag either vertical divider to resize columns and the horizontal divider above the composer to adjust its height. Divider positions are saved in the application data directory and survive restarts. Keyboard users can focus dividers and use arrow keys.

The editor displays addresses, editable hexadecimal bytes and decoded ASCII on aligned rows. It supports 8/16 bytes per row, paged viewing, UTF-8 or hex search, go-to-offset, undo/redo of individual byte edits, replacement of the complete buffer from hex, a numeric byte inspector, original/candidate comparison and candidate export. This release supports files up to 16 MiB and shows up to 64 rows per byte page. One file is active at a time; earlier sessions are available under **File → Recent sessions**. The most recent active session reopens on launch; target, provider, model and ordered prompt selections are saved per project.

## A protected change

1. Open a file. Hexwise immediately creates a project directory and an exact protected original snapshot. The original file remains untouched. Opening an external file waits outside the project lock, so slow file access cannot block other sessions. A 30-second access timeout reports stalled reads.
2. Inspect or edit bytes. **Save candidate** creates a new snapshot, not an overwrite of the original. Changing the full buffer from hex clears the per-byte undo stack; saved snapshots remain available.
3. Choose the target architecture/platform. Header detection suggests a profile; confirm the OS, ABI, instruction features and runtime. A CPU header cannot fully identify an ABI or platform. Set **Project → Target & verification contract** for signatures, dependencies and acceptance criteria.
4. Choose a provider, discover or enter its model ID, and describe a feature or edit. Cloud requests include up to the selected 4, 16 or 64 KiB of file bytes from the current byte page, the exact candidate digest and recent project conversation. Use Ollama for a local model endpoint.
5. The model returns analysis, a checked equal-length patch or a complete replacement. Hash, range and expected-byte checks run before a separate candidate is saved. A replacement requires the model to have received the full file context. Unknown or malformed responses are retained in the conversation and do not silently edit bytes.
6. Review **Changes**, run checks, and preview or test the candidate. These actions do not promote it.
7. **Accept & replace** asks for explicit acceptance, verifies the current original digest, saves an exact backup, then atomically replaces the original while retaining its permission bits. If another program changed the original, acceptance stops. Keep other writers quiescent during acceptance; this is not a cross-process locking system.

Each accepted replacement has its own backup, and earlier snapshots remain. Snapshot restoration creates a new candidate and does not overwrite the primary file. **Project → Project & recovery** shows the session directory, original identity and latest backup path. Binary replacement does not restore external application databases, settings or data migrations. File ownership, extended attributes, platform signatures and notarization are not regenerated by accepting a patch.

## Providers

Adapters are included for OpenAI Responses, Anthropic Messages, Gemini, Ollama Chat, and OpenAI-compatible endpoints. Connection presets include DeepSeek, Mistral, Groq and xAI. Availability depends on your provider account and model ID; listing a model does not guarantee generation access. Model IDs are discovered at runtime or entered explicitly.

Environment variables are `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` or `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `MISTRAL_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY` and `HEXWISE_API_KEY` for a custom compatible endpoint. Ollama uses its documented [JSON output mode](https://docs.ollama.com/capabilities/structured-outputs) to improve response formatting. Invalid proposals still fail the same independent byte checks. Ollama defaults to `http://127.0.0.1:11434` and requires an already running Ollama service and an installed model. Remote endpoints require HTTPS.

The 31 target prompts are baked into `profiles/`, with a separate web-document profile for source-based GUI starters. The desktop adapter explicitly replaces their draft response-format instructions while retaining the architecture guidance. These application responses are not interchangeable with the earlier framework CLI protocol. Prompts guide generation; the byte writer does not prove ISA, ABI, loader or feature correctness.

## GUI templates and prompt chains

**GUI templates** creates working standalone HTML starters: a configurable dashboard grid, sidebar/detail interface, master/detail view and developer workspace. A 4 × 4 grid creates sixteen panels; dimensions from 1 to 8 are available. These are source-based web starters, not generated native executables. Native GUI construction needs the selected platform's runtime, imports, packaging and signing contract.

The right-hand **Prompts** tab lets you choose a GUI layout, set its rows and columns, search and select feature prompts, inspect their instructions, and reorder or remove steps in the active chain. Selecting prompts prepares the request without editing the file or sending it to a model. **Manage prompts** opens the existing prompt editor.

The prompt library includes layout, navigation, search, local persistence, accessibility, settings, validation and a verification-plan extension. Select extensions in execution order under **Add prompt chain**. Each step receives the latest saved candidate and its exact digest, invokes the selected model, retains the response and saves any checked change as a new snapshot. Failed proposals stop the chain. **Stop** prevents further changes from being applied and retains the current provider response when it arrives; it does not immediately abort the provider network request. Applied earlier steps remain available for review. The verification-plan extension asks for analysis; it is not an independent test oracle.

**Prompt extension manager** creates and edits local feature prompts. Its library persists in the application data directory. Custom prompts can be deleted, and edited built-in prompts can be reset to their original instructions. Custom extensions influence a model request; they cannot grant execution privileges or run shell commands.

## Preview and testing

HTML/SVG candidates preview in a frame without same-origin privileges. The preview permits inline scripts for template interaction with restrictive content security rules for resource loads, fetch requests and forms. Preview URLs use short-lived capabilities scoped to one saved snapshot, not the API session credential. Interactive previews are for trusted project code; an iframe is not a substitute for a VM when evaluating hostile applications. Text previews display decoded content. Native files are never launched directly on the host by the preview action.

**Check candidate** reports identity and size, and checks basic ELF, PE, Mach-O and WebAssembly header/table bounds. Document checks include UTF-8 decoding, JSON syntax and Python syntax as applicable. Check results are retained with the exact snapshot. These are bounded format checks, not a full loader validator; signatures, ABI and behavior require independent validation and a matching runner.

**Project → Run in isolated Linux container** can execute complete Linux x86-64 or ARM64 ELF candidates using a locally installed Docker CLI/daemon and an already available matching runtime image. It disables networking, uses a read-only filesystem and candidate mount, drops capabilities, runs as a non-root user, limits memory/CPU/processes, limits captured output to 64 KiB and times out after 15 seconds. Optional expected stdout gives one explicit input/output check. It does not pull images. Docker availability and a suitable image must be established before use. Native macOS, Windows, firmware, raw function and device tests require other target runners. Containers share a kernel; use disposable VMs for adversarial or higher-risk binaries.

## Git and GitHub

The built-in console offers status, diff summary, history, fetch, initialization, branch creation, explicit staging, commits and push through the installed Git CLI. Actions operate on the directory shown in the console. **Stage all** includes all nonignored changes in that directory; inspect status first. Git authentication and commit identity come from your installed Git setup. No model response can invoke these actions.

GitHub actions show repository information, list pull requests, open the repository and create a draft PR. Set `GITHUB_TOKEN` or `GH_TOKEN`, or enter a session token in connections, for private repositories and write operations. The desktop application does not inherit the Codex GitHub connector. Publication and PR creation are explicit user actions; there is no automatic commit, push or merge.

## Files and implementation

- `server.py` serves the loopback application and authenticated API.
- `core.py` manages projects, snapshots, proposals, backups and atomic replacement.
- `providers.py` normalizes cloud/local provider requests.
- `preferences.py` stores validated non-secret workspace and project settings.
- `templates.py` supplies four distinct, interactive GUI starters.
- `validation.py` performs bounded file-format and document-syntax checks.
- `runner.py` supplies the explicit restricted Linux container runner.
- `web/` contains the dependency-free interface.
- `profiles/` contains the architecture/platform prompts and provenance references.
- `macos/` contains the native WebKit shell and procedural app icon source.
- `tests/` covers transaction failures, backup retention, prompt chains and provider request shapes.

macOS data is stored under `~/Library/Application Support/Hexwise`; portable Linux/Windows service defaults use `~/.local/share/hexwise`. `--data-dir` overrides it. The native app's default workspace is its `Workspace` subdirectory. Project directories hold metadata, chat messages, immutable-by-convention snapshot files, acceptance backups and runner results. Treat them as sensitive project material; this release does not encrypt them or garbage-collect them automatically.

The HTTP service binds only to loopback on an ephemeral port and authenticates API calls using a random per-launch token. The token is passed to the desktop view through a private process pipe. API credentials remain server-side. There is no telemetry or hosted service. Browser session storage holds only the per-launch local session token. Non-secret preferences are saved server-side; provider keys remain in memory or the environment.

## Build and verify

```sh
python3 -m unittest discover -s tests -v
node --check web/app.js
node tests/test_ui.js
bash build-macos.sh /absolute/path/to/New-Hexwise.app
```

Building the macOS shell requires Apple's command-line developer tools and Python 3.9 or newer. The output path must not exist. Build caches use a temporary directory. The resulting app targets the build host architecture and uses an ad-hoc signature. [The public validation summary](../docs/VALIDATION.md) records checks and remaining limitations.

Provider APIs follow their primary documentation: [OpenAI Responses](https://developers.openai.com/api/docs/guides/text), [Anthropic Messages](https://platform.claude.com/docs/en/api/messages/create), [Gemini content generation](https://ai.google.dev/api/generate-content), and [Ollama Chat](https://docs.ollama.com/api/chat). The complete original concept remains in the [Hexwise repository](https://github.com/woodyk/concepts-and-proofs/tree/main/concepts/direct-binary-software).

## Interactive clarification and research contracts

Studio uses an interactive draft adapter: select a target, describe the desired behavior, and answer the model’s questions in chat. An empty native file requires clarification about the application or function, deployment target, interfaces, imports, layout, signing and acceptance checks before byte generation. Save reusable requirements under **Project → Target & verification contract**. GUI starters use the **Web document** profile.

The standalone architecture prompts retain their strict frozen research-task protocol. Studio extracts their architecture, byte and validation rules without importing the research bookkeeping gate. It does not claim an interactive draft is a frozen evaluation. Missing-input responses stop prompt chains, preserve the candidate, and display readable questions; the raw response remains in project history.
