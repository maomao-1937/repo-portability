# repo-portability

[![tests](https://github.com/maomao-1937/repo-portability/actions/workflows/tests.yml/badge.svg)](https://github.com/maomao-1937/repo-portability/actions/workflows/tests.yml)

Check repository path spellings for common Windows naming conflicts before a cross-platform checkout. Python 3.11+; standard library only. Default mode also requires Git.

## Quickstart

Run from this repository directory. No package installation is needed; use `python3` if that is your Python 3 launcher.

```sh
python repo_portability.py . --paths-file examples/paths-clean.json --format json
python repo_portability.py . --paths-file examples/paths-risky.json --format json
python repo_portability.py . --directory --format json
python -m unittest discover -s tests -v
```

The clean sample exits 0, risky sample intentionally exits 1, and directory mode should exit 0 for an unchanged repository. Synthetic samples let Windows users audit spellings that cannot be created through ordinary Windows file APIs.

For a real Git repository:

```sh
python repo_portability.py /path/to/repo --format json
python repo_portability.py /path/to/repo --max-path 180 --format json
```

Replace `/path/to/repo` with your actual path; Windows paths with spaces need quotes. Default mode runs `git -C ROOT ls-files -z` and checks tracked path strings, including a tracked symlink's name without opening its target. Git failure exits 2. No checkout or rename is performed.

## Checks and modes

Checks include forbidden Windows characters/control characters, trailing dot/space, reserved device basenames even with extensions (`CON.txt`, `COM1.log`, superscript 1/2/3 forms), casefold collisions in file and parent-directory names, and file/directory collisions such as `a` versus `A/child`.

`--paths-file FILE` reads a UTF-8 JSON array of relative file path strings. It inspects spellings, without requiring those files to exist. Duplicate, empty, absolute and traversal paths are setup errors. `--directory` includes untracked files, excludes links/junctions and skips directories named `.git`, `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.next`, `.tox`. Empty directories are not listed. The two flags are mutually exclusive. Reports use escaped JSON so unusual path characters cannot inject terminal lines.

`--max-path N` is an optional relative-path character-count advisory. It does not include the checkout root, count UTF-16 units, model filesystem component limits, or guarantee compatibility with MAX_PATH or long-path APIs. Casefold is a conservative string heuristic, not a complete simulation of any particular filesystem's case rules or Unicode normalization.

Limits: 100000 paths, 16 MiB JSON/Git listing input, 32768 characters per path; Git invocation timeout 30 seconds. The root must exist and must not itself be a symlink/junction. Directory mode does not traverse child links. Keep the tree stable during a scan.

| Exit | Meaning |
| --- | --- |
| 0 | No implemented naming findings |
| 1 | One or more findings/advisories |
| 2 | Invalid arguments/paths, bounds, traversal, or Git failure |

## 中文快速开始

先用上方 `--paths-file` 样例验证运行环境：干净样例返回 0，风险样例返回 1。实际仓库默认读取 Git 跟踪的路径；若希望检查未跟踪文件，使用 `--directory`。程序只报告问题，不重命名文件。目录大小写冲突也会被检查；长度阈值只计算相对路径字符数，不能当作 Windows 长路径兼容保证。

## Scope

No content inspection, automatic fixes, permission checks, exhaustive platform emulation, archive validation, submodule recursion, or promise that a clean repository will check out on every host. See [RESEARCH.md](RESEARCH.md) and [TESTING.md](TESTING.md). MIT license.
