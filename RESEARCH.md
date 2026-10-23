# Research and decision record

Source review: 2026-10-23 (Asia/Singapore). Results are a naming heuristic, not a complete checkout guarantee.

## Observed facts

- [Microsoft: Naming Files, Paths, and Namespaces](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file) lists reserved device names (including names with extensions and superscript digit forms), prohibited characters, and trailing dot/space restrictions. The CLI implements a conservative subset of these concerns.
- [Git ls-files documentation](https://git-scm.com/docs/git-ls-files) documents tracked-path listing and NUL-delimited output with `-z`; this is the default input source.
- Locally implemented behavior: per-component naming checks, casefold spelling comparisons across parent prefixes, and file/directory role collisions. Synthetic arrays permit testing names that ordinary Windows file creation cannot represent. See TESTING.md.

## Inference and chosen boundary

An offline pre-check may catch common naming failures before a Windows collaborator checks out a repository. This is a proposed use, not measured user demand. Git supplies names but does not turn this scanner into a filesystem emulator. A relative character threshold is only an optional advisory, not a MAX_PATH guarantee.

## Alternatives and unknowns

Use git ls-files directly for tracked-path inventory; use a disposable checkout and real build/test job on each supported operating system for broader compatibility evidence. Casefold differs from some filesystem case rules; Unicode normalization, 8.3 aliases, permissions, and API-specific path limits are outside this implementation. Adoption, time saved, universal Windows coverage, and Linux/macOS execution are unknown. No novelty, popularity, or completeness claim is made.
