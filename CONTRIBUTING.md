# Contributing to Hexwise

**Wadih Frederick Khairallah — 2b0n2b!!!**  
AI-assisted project guidance.

Start with a bounded problem and a reproducible fixture. State the target architecture, executable format, ABI, expected behavior, retained behavior, data and recovery assumptions. Link actual evidence to the exact candidate and commit.

Keep provider keys and local project material out of the repository. Do not include private conversations, account audits, environment files or personal binaries in test fixtures. Use temporary files for integration tests.

Preserve original snapshots and the explicit acceptance boundary. A model response must never implicitly overwrite originals, publish Git changes or execute a program. Add meaningful regression checks when fixing failures in these boundaries.

Before submitting:

```sh
python3 -m unittest discover -s studio/tests -v
python3 -m unittest discover -s framework/tests -v
node --check studio/web/app.js
node studio/tests/test_ui.js
python3 tools/integrity.py --update
python3 tools/integrity.py --check
```

Keep the Studio profiles and standalone framework prompts synchronized. Record unsupported, failed and not-run results explicitly. Distinguish full model-emitted executables, packaged payloads, source-based templates and exports of existing binaries.

Do not claim improved efficiency or broad model capability from a serialization test. Propose independent behavioral checks and comparable source/compiler or assembly baselines. Preserve attribution and relevant third-party provenance.
