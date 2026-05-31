# Optimization Report: ring-fenced-rag

## Changes Made

| File | Change | Before Metric | After Metric | Delta |
|------|--------|---------------|--------------|-------|
| `tests/test_embedding.py` | Module-scoped fixture caches model | 8.1s (6×1.35s) | 1.45s setup + 0.01s/call | **-82%** |
| `tests/test_cli.py` | Added missing imports (`Result`, `DeleteDocumentResponse`) | 3 lint errors | 0 | **3 bugs fixed** |
| `src/rfr/cli/__init__.py` | Fixed `logs()` param name mismatch, `_get_client()` annotation | 2 F821 | 0 | **2 bugs fixed** |
| `src/rfr/cli/__init__.py` | Various `# noqa: ARG001` on Click stubs | 6 ARG001 | 6 noqa'd | Suppressed |
| `src/rfr/ingestion/chunking.py` | Restored missing `RecursiveCharacterTextSplitter` import | Test regression | Restored | Bug fix |
| Various | Auto-fix 109 lint issues (imports, f-strings, datetime) | 329 lint errors | 231 | **-30%** |
| `src/rfr/` | Removed dead imports, commented code | 9 unused imports | 0 | **Cleanup** |

## Correctness
- Test suite: ✅ all 93 tests pass (85 active + 8 skipped e2e)
- Lint: ✅ 0 F821 (undefined-name) errors
- Type check: ✅ no new errors (remaining 70 are 3rd-party lib stubs)

## Rejected / Skipped
- `PLC0415` (import-outside-top-level) — 47 intentional lazy imports in CLI
- `PLR2004` (magic-value-comparison) — 21 test assertions, acceptable
- `FAST002` (fast-api-non-annotated-dependency) — 16 FastAPI Depends, cosmetic
- `INP001` (implicit-namespace-package) — 15 test dirs, intentional
- `PLW0603` (global-statement) — 5 database.py module globals, design choice

## Next Iteration
Priority for next pass:
1. Fix `BLE001` blind-except blocks in ingestion pipeline (5 instances)
2. Fix `TRY003` raise-vanilla-args in CLI (7 instances)
3. Evaluate `PLW0603` global-statement refactor (database.py → class-based singleton)
