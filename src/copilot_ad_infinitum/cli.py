"""CLI entry point for copilot-ad-infinitum."""

import argparse
import asyncio
import os

from .loop import run_loop
from .tasks import load_tasks

from rich.console import Console

console = Console()


def main():
    parser = argparse.ArgumentParser(
        prog="copilot-ad-infinitum",
        description="Autonomous task cycling with GitHub Copilot",
    )
    parser.add_argument(
        "task_source",
        help="Folder of task files (.md, .py, .sh) or a single task file",
    )
    parser.add_argument(
        "-c", "--cycles",
        type=int,
        default=None,
        help="Number of cycles, 0 = infinite (env: COPILOT_CYCLES, default: 1)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Copilot model ID (env: COPILOT_MODEL_ID, default: gpt-5.4)",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=None,
        help="Seconds between cycles (env: COPILOT_COOLDOWN, default: 0)",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=None,
        help="Seconds to wait for session idle (env: COPILOT_TIMEOUT, default: 3600)",
    )
    parser.add_argument(
        "--inject-folder",
        type=str,
        nargs="?",
        const=".",
        default=None,
        help="Inject directory tree into prompts (no value = cwd, or specify path; env: COPILOT_INJECT_FOLDER, default: off)",
    )
    args = parser.parse_args()

    # Resolve from args -> env -> defaults
    model_id = args.model or os.environ.get("COPILOT_MODEL_ID", "gpt-5.4")
    cycles = args.cycles if args.cycles is not None else int(os.environ.get("COPILOT_CYCLES", "1"))
    cooldown = args.cooldown if args.cooldown is not None else int(os.environ.get("COPILOT_COOLDOWN", "0"))
    timeout = args.timeout if args.timeout is not None else int(os.environ.get("COPILOT_TIMEOUT", "3600"))

    # Resolve inject-folder: CLI arg -> env var -> off
    if args.inject_folder is not None:
        inject_folder = os.path.abspath(args.inject_folder)
    else:
        env_val = os.environ.get("COPILOT_INJECT_FOLDER", "")
        if env_val and env_val.lower() != "false":
            inject_folder = os.path.abspath(env_val if env_val.lower() != "true" else ".")
        else:
            inject_folder = None

    # Load tasks
    console.print("[dim]Loading tasks...[/]")
    tasks = load_tasks(args.task_source)

    # Run
    asyncio.run(run_loop(tasks, model_id, cycles, cooldown, timeout, inject_folder))


if __name__ == "__main__":
    main()
