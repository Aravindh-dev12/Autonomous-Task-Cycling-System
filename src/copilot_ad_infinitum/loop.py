"""Core autonomous loop with signal handling and Rich output."""

import asyncio
import os
import signal
import subprocess
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from .runner import run_prompt
from .tasks import TaskItem

console = Console()

# Graceful shutdown flag
_stop_requested = False


def _signal_handler(signum, frame):
    global _stop_requested
    if _stop_requested:
        console.print("\n[bold red]Double Ctrl+C: aborting immediately.[/]")
        sys.exit(1)
    _stop_requested = True
    console.print("\n[yellow]Ctrl+C received. Will stop after current task finishes.[/]")


def _run_script(task: TaskItem) -> subprocess.CompletedProcess:
    """Execute a .py or .sh script directly via subprocess."""
    if task.kind == "python":
        cmd = [sys.executable, task.path]
    elif task.kind == "shell":
        cmd = ["bash", task.path]
    else:
        raise ValueError(f"Unknown script kind: {task.kind}")
    return subprocess.run(cmd)


def print_banner(model_id: str, task_count: int, cycles: int, cooldown: int, timeout: int, inject_folder: str | None):
    cycles_str = str(cycles) if cycles > 0 else "infinite"
    inject_str = inject_folder if inject_folder else "off"
    console.print(
        Panel.fit(
            f"[bold]COPILOT AD-INFINITUM[/] - Autonomous Agents\n"
            f"Model: [cyan]{model_id}[/]\n"
            f"Tasks: [green]{task_count}[/] | "
            f"Cycles: [green]{cycles_str}[/] | "
            f"Cooldown: {cooldown}s | "
            f"Timeout: {timeout}s\n"
            f"Inject folder: {inject_str}",
            border_style="blue",
        )
    )
    console.print(
        Panel.fit(
            "[bold red]EXTREME SECURITY RISK[/]\n"
            "Running autonomously with full system access.\n"
            "Only run inside a securely isolated environment.\n"
            "[bold]USE AT YOUR OWN RISK.[/]",
            border_style="red",
        )
    )
    console.print("[dim]Press Ctrl+C to stop after current task. Double Ctrl+C to abort.[/]\n")


async def run_loop(
    tasks: list[TaskItem],
    model_id: str,
    cycles: int,
    cooldown: int,
    timeout: int = 3600,
    inject_folder: str | None = None,
):
    """Core autonomous loop: cycles x tasks, fresh Copilot session per prompt task."""
    signal.signal(signal.SIGINT, _signal_handler)

    print_banner(model_id, len(tasks), cycles, cooldown, timeout, inject_folder)

    # Prepare tree injection function
    if inject_folder:
        from smolagents.bp_tools import inject_tree as _inject_tree
        tree_suffix = _inject_tree(folder=inject_folder)
    else:
        tree_suffix = ""

    total_start = time.time()
    cycle = 0
    total_tasks_run = 0

    while cycles == 0 or cycle < cycles:
        cycle += 1
        cycle_limit = f"/{cycles}" if cycles > 0 else ""

        console.print(Rule(f"[bold]Cycle {cycle}{cycle_limit}[/]", style="blue"))

        for task_idx, task in enumerate(tasks):
            if _stop_requested:
                break

            task_label = f"Task {task_idx + 1}/{len(tasks)} ({task.name})"
            console.print(f"[dim]{task_label} starting...[/]")

            task_start = time.time()

            if task.kind == "prompt":
                try:
                    prompt = task.content + tree_suffix
                    result = await run_prompt(prompt, model_id, timeout)
                    elapsed = time.time() - task_start
                    total_tasks_run += 1
                    console.print(f"[green]OK[/] {task_label} | {elapsed:.1f}s")
                except KeyboardInterrupt:
                    console.print(f"[yellow]{task_label} interrupted.[/]")
                    break
                except Exception as e:
                    elapsed = time.time() - task_start
                    total_tasks_run += 1
                    console.print(f"[red]FAIL[/] {task_label} | {elapsed:.1f}s | {e}")
            else:
                try:
                    result = _run_script(task)
                    elapsed = time.time() - task_start
                    total_tasks_run += 1
                    if result.returncode == 0:
                        console.print(f"[green]OK[/] {task_label} | {elapsed:.1f}s | exit 0")
                    else:
                        console.print(f"[red]FAIL[/] {task_label} | {elapsed:.1f}s | exit {result.returncode}")
                except KeyboardInterrupt:
                    console.print(f"[yellow]{task_label} interrupted.[/]")
                    break
                except Exception as e:
                    elapsed = time.time() - task_start
                    total_tasks_run += 1
                    console.print(f"[red]FAIL[/] {task_label} | {elapsed:.1f}s | {e}")

        if _stop_requested:
            console.print(f"\n[yellow]Stopped after cycle {cycle}.[/]")
            break

        if cooldown > 0 and (cycles == 0 or cycle < cycles):
            console.print(f"[dim]Cooldown: {cooldown}s...[/]")
            await asyncio.sleep(cooldown)

    # Session summary
    total_elapsed = time.time() - total_start
    console.print()
    console.print(Rule("[bold]Session Summary[/]", style="green"))
    console.print(f"  Cycles completed: [green]{cycle}[/]")
    console.print(f"  Tasks run: [green]{total_tasks_run}[/]")
    console.print(f"  Total time: [green]{total_elapsed:.1f}s[/]")
