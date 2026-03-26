# Copilot Ad-Infinitum

Autonomous task cycling with GitHub Copilot. Loads tasks from a folder of task files (`.md`, `.py`, `.sh`) or a single file and runs them repeatedly using GitHub Copilot with full system access.

## Installation

```bash
pip install -e .
```

Requires the `copilot` Python SDK and a valid GitHub Copilot authentication.

## Usage

```bash
copilot-ad-infinitum ./tasks/                         # Run all task files, 1 cycle
copilot-ad-infinitum ./tasks/ -c 0                    # Run forever
copilot-ad-infinitum ./tasks/ -c 5 --cooldown 10      # 5 cycles, 10s cooldown
copilot-ad-infinitum ./single-task.md                 # Run a single prompt
copilot-ad-infinitum ./setup.sh                       # Run a single script
copilot-ad-infinitum ./tasks/ -m gpt-5.4              # Specify model
copilot-ad-infinitum ./tasks/ -t 3600                 # 1 hour timeout
copilot-ad-infinitum ./tasks/ --inject-folder         # Inject cwd tree into prompts
copilot-ad-infinitum ./tasks/ --inject-folder /src    # Inject specific folder tree
```

### CLI Options

| Option | Description | Default |
|---|---|---|
| `task_source` | Folder of task files or a single file | (required) |
| `-c`, `--cycles` | Number of cycles, 0 = infinite | 1 |
| `-m`, `--model` | Copilot model ID | gpt-5.4 |
| `--cooldown` | Seconds to wait between cycles | 0 |
| `-t`, `--timeout` | Seconds to wait for session idle | 3600 |
| `--inject-folder` | Inject directory tree into prompts (no value = cwd, or specify path) | off |

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `COPILOT_MODEL_ID` | Copilot model ID | gpt-5.4 |
| `COPILOT_CYCLES` | Number of cycles, 0 = infinite | 1 |
| `COPILOT_COOLDOWN` | Seconds between cycles | 0 |
| `COPILOT_TIMEOUT` | Seconds to wait for session idle | 3600 |
| `COPILOT_INJECT_FOLDER` | Inject directory tree (`true` = cwd, `false` = off, or a path) | false |

CLI arguments take precedence over environment variables.

## Task Files

### Supported file types

- **`.md`** -- Agent prompts sent to GitHub Copilot
- **`.py`** -- Executed directly via the Python interpreter (subprocess)
- **`.sh`** -- Executed directly via bash (subprocess)

### Folder conventions

```
tasks/
├── _preamble.md          (optional) prepended to ALL prompt tasks
├── 01-setup-env.sh       script: install deps, create/clean dirs
├── 02-implement.md       prompt: Copilot does the work
├── 03-validate.py        script: programmatic validation
├── 04-refine.md          prompt: Copilot fixes issues
└── _postamble.md         (optional) appended to ALL prompt tasks
```

- Files are loaded in **alphabetical order**
- Files starting with `_` are **modifiers**, not tasks
- `_preamble.md` content is prepended to every `.md` prompt task
- `_postamble.md` content is appended to every `.md` prompt task

### Single file mode

You can pass a single `.md`, `.py`, or `.sh` file instead of a folder.

## Custom Tools

In addition to Copilot's built-in tools (bash, file I/O, URL fetching), every session includes custom tools powered by [bpsa](https://github.com/joaopauloschuler/beyond-python-smolagents):

| Tool | Description |
|---|---|
| `list_directory_tree` | Tree view of a directory with file line counts and optional function/class signatures |
| `show_signatures` | Extract function and class signatures from a source file |
| `search_in_files` | Grep-like search across folders with file paths and line numbers |
| `inject_tree` | Directory tree with signatures and LLM guidance text |
| `compare_files` | Unified diff between two files |
| `compare_folders` | Diff all source files across two directories |
| `count_lines_of_code` | Lines of code stats broken down by file extension |

## How It Works

For each cycle, tasks are executed sequentially:

1. **Prompt tasks** (`.md`): A fresh GitHub Copilot session is created with `PermissionHandler.approve_all`, the prompt is sent, and the response is awaited. The session is then closed. Copilot has full access to read/write files, execute shell commands, fetch URLs, and use memory.

2. **Script tasks** (`.py`, `.sh`): Executed directly via subprocess. Useful for setup, validation, and cleanup steps.

If a task fails, the error is printed and execution continues to the next task. Press `Ctrl+C` once to stop after the current task, or twice to abort immediately.

## Programmatic Usage

```python
import asyncio
from copilot_ad_infinitum.tasks import load_tasks
from copilot_ad_infinitum.loop import run_loop

tasks = load_tasks("./tasks/")
asyncio.run(run_loop(tasks, model_id="gpt-5.4", cycles=3, cooldown=10, inject_folder="/path/to/project"))
```

## Security Warning

This tool runs GitHub Copilot autonomously with **full system access** (file read/write, shell execution, URL fetching). Only run inside a securely isolated environment.

## License

MIT
