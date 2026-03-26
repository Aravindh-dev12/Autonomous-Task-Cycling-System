"""Task loading from folders and files."""

import glob
import os
import sys
from dataclasses import dataclass

from rich.console import Console

console = Console()

_EXTENSION_TO_KIND = {".md": "prompt", ".py": "python", ".sh": "shell"}


@dataclass
class TaskItem:
    """A single task: either a Copilot prompt or an executable script."""

    name: str       # display name (file basename)
    kind: str       # "prompt" | "python" | "shell"
    content: str    # assembled prompt text (prompts) or raw content (scripts)
    path: str | None  # original file path (needed for script execution)


def _file_kind(filepath: str) -> str | None:
    """Return task kind for a file extension, or None if unsupported."""
    _, ext = os.path.splitext(filepath)
    return _EXTENSION_TO_KIND.get(ext.lower())


def load_tasks(path: str) -> list[TaskItem]:
    """Load tasks from a folder of task files (.md, .py, .sh) or a single file.

    Folder mode:
        - _preamble.md and _postamble.md are optional wrappers (prompt tasks only)
        - All other *.md, *.py, *.sh files are tasks, sorted alphabetically
        - Each prompt task = preamble + file content + postamble
        - Script tasks (.py, .sh) are executed directly via subprocess

    File mode:
        - Returns a single-element list with a TaskItem.
    """
    if os.path.isdir(path):
        all_files = sorted(
            f
            for ext in ("*.md", "*.py", "*.sh")
            for f in glob.glob(os.path.join(path, ext))
        )
        if not all_files:
            console.print(f"[bold red]Error:[/] No task files (.md, .py, .sh) found in {path}")
            sys.exit(1)

        preamble = ""
        postamble = ""
        task_files = []

        for f in all_files:
            basename = os.path.basename(f)
            if basename == "_preamble.md":
                with open(f, "r", encoding="utf-8") as fh:
                    preamble = fh.read().strip() + "\n\n"
                console.print(f"  [green]Preamble:[/] {basename}")
            elif basename == "_postamble.md":
                with open(f, "r", encoding="utf-8") as fh:
                    postamble = "\n\n" + fh.read().strip()
                console.print(f"  [green]Postamble:[/] {basename}")
            elif not basename.startswith("_"):
                task_files.append(f)

        if not task_files:
            console.print(f"[bold red]Error:[/] No task files found in {path} "
                          "(files starting with '_' are modifiers, not tasks)")
            sys.exit(1)

        tasks = []
        for f in task_files:
            basename = os.path.basename(f)
            kind = _file_kind(f)
            with open(f, "r", encoding="utf-8") as fh:
                content = fh.read().strip()

            if kind == "prompt":
                content = preamble + content + postamble
                console.print(f"  [cyan]Task:[/] {basename}")
            else:
                console.print(f"  [magenta]Script ({kind}):[/] {basename}")

            tasks.append(TaskItem(name=basename, kind=kind, content=content, path=f))

        return tasks

    elif os.path.isfile(path):
        kind = _file_kind(path)
        if kind is None:
            console.print(f"[bold red]Error:[/] Unsupported file type: {path} (expected .md, .py, or .sh)")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
        if not content:
            console.print(f"[bold red]Error:[/] File is empty: {path}")
            sys.exit(1)
        basename = os.path.basename(path)
        if kind == "prompt":
            console.print(f"  [cyan]Task:[/] {basename}")
        else:
            console.print(f"  [magenta]Script ({kind}):[/] {basename}")
        return [TaskItem(name=basename, kind=kind, content=content, path=path)]

    else:
        console.print(f"[bold red]Error:[/] Path not found: {path}")
        sys.exit(1)
