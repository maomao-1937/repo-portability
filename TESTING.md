# Validation record

Executed on 2026-10-23 (Asia/Singapore), Windows, CPython 3.11.15. This records the actual local run, not future CI or another operating system.

## Unit tests

```sh
python -m unittest discover -s tests -v
```

Exit 0; 16 tests discovered, 15 passed, 1 skipped, zero failures/errors.

The symlink test was skipped because creating a symlink failed without the required Windows privilege. This is an untested environment-dependent branch, not a pass. Windows junction rejection has code-level checks but was not exercised by a dedicated junction fixture.

## CLI examples and exit contracts

Each top-level checks.json entry was executed from this repository root with the current Python executable. All expected return codes matched; exit 1/2 rows are intentional negative cases. Generated outputs may be replaced on repeat runs as specified by the command.

| Arguments after python | Expected exit | Actual exit |
| --- | --- | --- |
| `repo_portability.py --help` | 0 | 0 |
| `repo_portability.py . --paths-file examples/paths-clean.json --format json` | 0 | 0 |
| `repo_portability.py . --paths-file examples/paths-risky.json --format json` | 1 | 1 |
| `repo_portability.py . --paths-file examples/paths-invalid.json` | 2 | 2 |
| `repo_portability.py . --directory --format json` | 0 | 0 |

The test suite uses temporary directories and calls the root CLI directly. No network calls, package installation, credentials, or publication were needed.

## Limits of this evidence

Linux/macOS and other Python versions were not executed. No production workload, real-user adoption, performance benchmark, or hostile concurrent filesystem race has been validated. Re-run the commands on each intended environment.

Coverage includes casefold parent collisions, file/directory collisions, reserved names including superscript digits, forbidden characters/trailing dot-space, traversal/absolute paths, relative-length advisories, dependency-directory skips, Git-backed tracked listing in a temporary repository, non-Git errors, and CLI help.
