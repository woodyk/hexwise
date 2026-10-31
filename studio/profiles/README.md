# Hexwise architecture and platform prompts

This library supplies 31 standalone prompts: 28 native CPU and platform combinations and three WebAssembly environments. Each includes the shared Hexwise rules, target-specific ABI constraints, a JSON response contract and primary references. Choose one prompt and fill its companion task template before asking a model to generate or inspect bytes.

Concept attribution: **Wadih Frederick Khairallah — 2b0n2b!!!**. Draft created October 29, 2026. These are authored prompt profiles, not benchmarked capabilities. The existing `hexwise.py` still supports only `aarch64-leaf-u64-add-v1`; it does not accept these proposed `hexwise/prompt-0.2-draft` tasks or responses.

## Use a profile

1. Open the prompt for the exact CPU, OS and ABI below. Each text file is self-contained; no shared prompt needs to be appended.
2. Copy its task template, replace null values with the actual contract, and mark inapplicable fields explicitly. Pin platform versions and specification revisions. A generic CPU model or missing SDK is not enough for platform integration.
3. Select `create`, `read`, `update` or `delete`; feature deletion means a new candidate with retained behavior. Supply exact base bytes, digest and observations for every operation except create.
4. Choose `artifact_kind` and `production_path`. A raw function, complete executable, shared library, firmware image, core module and component need different validation. Full native executables require every container byte; a payload requires an explicit packaging contract.
5. Supply a host-computed digest of the frozen task separately as `task_sha256`. The digest mechanism must be shared by the host and evaluator; the model copies the value. Missing values should produce a structured `needs_input` response.
6. Save the response as an unverified proposal. A future adapter must validate its response format and target semantics before materialization or execution. Record actual tool and test results; the prompt alone cannot enforce them.

The task templates are intentionally incomplete and are not runnable examples. Empty base fields are appropriate for CREATE only. The profile fixes pointer width and endianness; a different choice requires a different profile. The current prompts restrict in-place patches to equal-length ranges; larger structural changes require full replacement artifacts. READ and feature removal describe the intended interface and need evaluator support of their own.

## Profile index

| Platform | Target | Prompt | Task template |
| --- | --- | --- | --- |
| linux | Linux x86-64 | [Prompt](linux/linux-x86_64.txt) | [Task](linux/linux-x86_64.task-template.json) |
| linux | Linux x86 32-bit | [Prompt](linux/linux-i386.txt) | [Task](linux/linux-i386.task-template.json) |
| linux | Linux ARM64 | [Prompt](linux/linux-aarch64.txt) | [Task](linux/linux-aarch64.task-template.json) |
| linux | Linux ARMv7 hard float | [Prompt](linux/linux-armv7hf.txt) | [Task](linux/linux-armv7hf.task-template.json) |
| linux | Linux RISC-V 64-bit | [Prompt](linux/linux-riscv64.txt) | [Task](linux/linux-riscv64.task-template.json) |
| linux | Linux POWER little-endian | [Prompt](linux/linux-ppc64le.txt) | [Task](linux/linux-ppc64le.task-template.json) |
| linux | Linux IBM Z | [Prompt](linux/linux-s390x.txt) | [Task](linux/linux-s390x.task-template.json) |
| windows | Windows x64 | [Prompt](windows/windows-x64.txt) | [Task](windows/windows-x64.task-template.json) |
| windows | Windows x86 32-bit | [Prompt](windows/windows-x86.txt) | [Task](windows/windows-x86.task-template.json) |
| windows | Windows ARM64 | [Prompt](windows/windows-arm64.txt) | [Task](windows/windows-arm64.task-template.json) |
| windows | Windows ARM64EC | [Prompt](windows/windows-arm64ec.txt) | [Task](windows/windows-arm64ec.task-template.json) |
| apple | macOS Apple silicon | [Prompt](apple/macos-arm64.txt) | [Task](apple/macos-arm64.task-template.json) |
| apple | macOS Intel | [Prompt](apple/macos-x86_64.txt) | [Task](apple/macos-x86_64.task-template.json) |
| apple | iOS and iPadOS devices | [Prompt](apple/ios-arm64.txt) | [Task](apple/ios-arm64.task-template.json) |
| apple | iOS simulator on Apple silicon | [Prompt](apple/ios-simulator-arm64.txt) | [Task](apple/ios-simulator-arm64.task-template.json) |
| apple | iOS simulator on Intel | [Prompt](apple/ios-simulator-x86_64.txt) | [Task](apple/ios-simulator-x86_64.task-template.json) |
| android | Android ARM64 | [Prompt](android/android-arm64-v8a.txt) | [Task](android/android-arm64-v8a.task-template.json) |
| android | Android ARMv7 | [Prompt](android/android-armeabi-v7a.txt) | [Task](android/android-armeabi-v7a.task-template.json) |
| android | Android x86-64 | [Prompt](android/android-x86_64.txt) | [Task](android/android-x86_64.task-template.json) |
| android | Android x86 32-bit | [Prompt](android/android-x86.txt) | [Task](android/android-x86.task-template.json) |
| freebsd | FreeBSD amd64 | [Prompt](freebsd/freebsd-amd64.txt) | [Task](freebsd/freebsd-amd64.task-template.json) |
| freebsd | FreeBSD ARM64 | [Prompt](freebsd/freebsd-aarch64.txt) | [Task](freebsd/freebsd-aarch64.task-template.json) |
| embedded | Bare metal Cortex-M0 and M0+ | [Prompt](embedded/baremetal-cortex-m0.txt) | [Task](embedded/baremetal-cortex-m0.task-template.json) |
| embedded | Bare metal Cortex-M4 | [Prompt](embedded/baremetal-cortex-m4.txt) | [Task](embedded/baremetal-cortex-m4.task-template.json) |
| embedded | Bare metal RISC-V 32-bit | [Prompt](embedded/baremetal-rv32.txt) | [Task](embedded/baremetal-rv32.task-template.json) |
| embedded | Bare metal RISC-V 64-bit | [Prompt](embedded/baremetal-rv64.txt) | [Task](embedded/baremetal-rv64.task-template.json) |
| uefi | UEFI x64 applications | [Prompt](uefi/uefi-x64.txt) | [Task](uefi/uefi-x64.task-template.json) |
| uefi | UEFI AArch64 applications | [Prompt](uefi/uefi-aarch64.txt) | [Task](uefi/uefi-aarch64.task-template.json) |
| webassembly | WebAssembly in a browser | [Prompt](webassembly/wasm32-browser.txt) | [Task](webassembly/wasm32-browser.task-template.json) |
| webassembly | WebAssembly WASI Preview 1 | [Prompt](webassembly/wasm32-wasip1.txt) | [Task](webassembly/wasm32-wasip1.task-template.json) |
| webassembly | WebAssembly WASI 0.2 components | [Prompt](webassembly/wasm32-wasip2.txt) | [Task](webassembly/wasm32-wasip2.task-template.json) |

## Important target distinctions

The same ISA does not imply the same ABI. Windows x64 uses different argument and stack rules from System V AMD64. Apple ARM64 has platform-specific calling rules. Android native code uses Android ABIs and Bionic, and Android ARMv7 softfp linkage differs from Linux armhf. Arm64EC requires its own interoperation rules. Device and simulator Mach-O platform identities also differ. The per-profile references identify the governing specifications.

ISA and data encoding need separate treatment. Linux s390x is the big-endian profile here. Thumb and RISC-V may have mixed instruction lengths; x86 instructions are variable length. WebAssembly is a virtual ISA with structured module/component formats and variable-length integer encodings. A universal four-byte patch rule would corrupt several of these targets.

## Coverage and extensions

The selection covers mainstream desktop/mobile targets, major Linux server families, two FreeBSD targets, common ARM/RISC-V firmware families and UEFI. Architecture coverage is not a promise of support by any particular OS release, SDK, model or runner. Intel simulator and 32-bit targets require an environment that still supports them.

MIPS, SPARC, 32-bit PowerPC, AVR, Xtensa, GPUs, DSPs, legacy BIOS, kernels, drivers and real-time OS ABIs need additional profiles with their exact execution contracts. ESP32 RISC-V boards can use the bare-metal RV32 prompt only with their board-specific boot/memory contract; ESP-IDF/FreeRTOS integration and Xtensa variants need separate ABI/runtime profiles. ARM64EC is included separately; arm64e, ARM64_32 and reduced-register RISC-V E variants are not silently covered by a nearby name.

To add a profile, specify the ISA/mode, pointer width, instruction/data byte order, ABI, container, platform version requirements, integration rules and primary specifications. Then add a matching task template and target validator/runner. Only set runner support after independent execution evidence exists. Split training data by target and originating program family, and preserve the profile ID in each record.

## References and review

`profiles.json` is the machine-readable registry. The primary references below informed the ABI distinctions and are included in each relevant prompt. Freeze the actual revisions when building an experiment; specification links may move. Profile validation here checks document completeness and registry consistency, not generated machine-code correctness. No new model or platform execution benchmark has been run.

- [Intel instruction reference](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [System V x86-64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [System V i386 psABI](https://gitlab.com/x86-psABIs/i386-ABI)
- [Arm ABI specifications](https://github.com/ARM-software/abi-aa)
- [Microsoft x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention)
- [Microsoft x86 calling conventions](https://learn.microsoft.com/en-us/cpp/cpp/argument-passing-and-naming-conventions)
- [Microsoft ARM64 ABI](https://learn.microsoft.com/en-us/cpp/build/arm64-windows-abi-conventions)
- [Microsoft Arm64EC](https://learn.microsoft.com/en-us/windows/arm/arm64ec)
- [Microsoft PE and COFF format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)
- [Apple ARM64 ABI differences](https://developer.apple.com/documentation/xcode/writing-arm64-code-for-apple-platforms)
- [Apple platform architecture differences](https://developer.apple.com/documentation/apple-silicon/addressing-architectural-differences-in-your-macos-code)
- [Apple Mach-O definitions](https://github.com/apple-oss-distributions/xnu/blob/main/EXTERNAL_HEADERS/mach-o/loader.h)
- [Android NDK ABI guide](https://developer.android.com/ndk/guides/abis)
- [RISC-V ELF psABI](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/)
- [RISC-V ISA specifications](https://docs.riscv.org/reference/isa/)
- [OpenPOWER ELFv2 ABI](https://github.com/OpenPOWERFoundation/ELFv2-ABI)
- [IBM s390x ELF ABI](https://ibm.github.io/s390x-abi/)
- [FreeBSD architecture handbook](https://docs.freebsd.org/en/books/arch-handbook/)
- [Zephyr Cortex-M architecture guide](https://docs.zephyrproject.org/latest/hardware/arch/arm_cortex_m.html)
- [UEFI calling conventions and platform bindings](https://uefi.org/specs/UEFI/2.10/02_Overview.html)
- [WebAssembly binary format](https://webassembly.github.io/spec/core/binary/index.html)
- [WASI interfaces and versions](https://github.com/WebAssembly/WASI)
- [WebAssembly Component Model](https://github.com/WebAssembly/component-model)
