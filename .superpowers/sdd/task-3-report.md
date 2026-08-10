# Task 3 Report: Serve llms.txt from the documentation site

## What I Implemented

- Added `docs/llms.txt` with the corrected description-first, URL-last convention.
- Replaced `DocsSiteAgentFileTests` with the corrected parser and terminal-URL assertion.
- Added `site/` to `.gitignore` so MkDocs output is not committed.
- Updated the Task 3 plan's test and content blocks to the corrected versions.

## Tests Run And Results

- `PATH=.venv313/bin:$PATH PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
  - GREEN: passed, `Ran 19 tests in 0.004s`, `OK`.
- `.venv313/bin/mkdocs build --strict && test -f site/llms.txt && echo "published"`
  - Passed and printed `published`.
  - MkDocs emitted existing informational messages about pages outside the navigation and a third-party Material for MkDocs warning; neither failed strict mode.

## TDD Evidence

### RED

Ran:

```text
PATH=.venv313/bin:$PATH PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v
```

Relevant failure:

```text
FAIL: test_docs_llms_txt_points_at_pages_that_exist ...
AssertionError: ' ' unexpectedly found in 'agents/agent-access-pack/: the readiness-first call sequence,' : the URL must end its line, so no prose follows it

Ran 19 tests in 0.006s
FAILED (failures=10)
```

This was expected because the original scratch `docs/llms.txt` placed descriptions after documentation URLs on the same line.

### GREEN

Ran the same focused command after replacing `docs/llms.txt`:

```text
Ran 19 tests in 0.004s
OK
```

## MkDocs Publication Check

```text
INFO    -  Building documentation to directory: .../site
INFO    -  Documentation built in 0.82 seconds
published
```

## Files Changed

- `.gitignore`
- `backend/tests/test_agent_surface.py`
- `docs/llms.txt`
- `docs/superpowers/plans/2026-08-10-pre-deploy-completion.md`

## Self-Review Findings

- The parser only records text following the documentation host prefix and rejects a space in every reference, enforcing the documented line format.
- Every referenced slug resolves to an existing Markdown source page.
- `mkdocs build --strict` copied `docs/llms.txt` to `site/llms.txt`.
- The intended commit scope contains only the four requested Task 3 files; generated `site/` output is ignored.

## Issues Or Concerns

- No implementation concerns. MkDocs printed pre-existing informational/warning output but completed successfully under `--strict`.

## Review Fix Report

### Changes

- Restored and verified the supplied description-first `docs/llms.txt` content; the Task 3 plan's `text` block matches it byte-for-byte.
- Changed the documentation URL parser to remove leading whitespace only, then reject trailing whitespace before resolving the page path.

### Regression Evidence

- With a deliberate trailing space after a documentation URL, the previous `.strip()` parser passed the URL test.
- After the parser and guard change, the same input failed with: `the URL must terminate the line without trailing whitespace`.

### Verification

```text
$ PATH=.venv313/bin:$PATH PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v
Ran 19 tests in 0.004s
OK

$ .venv313/bin/mkdocs build --strict && test -f site/llms.txt && echo "published"
INFO    -  Documentation built in 0.75 seconds
published
```

MkDocs also emitted its existing Material warning and notices for pages outside the configured navigation; `--strict` exited successfully.
