"""Copilot session management."""

from copilot import CopilotClient, PermissionHandler
from copilot.generated.session_events import SessionEventType
from rich.console import Console

from copilot_ad_infinitum.tools import ALL_COPILOT_TOOLS

console = Console()

#_SYSTEM_PREFIX = (
#    "You are an autonomous agent. When your task involves writing code, "
#    "you MUST also execute it using your shell tool and show the output. "
#    "Do not just return code — run it.\n\n"
#)

_SYSTEM_PREFIX = ""

def _event_handler(event):
    """Print real-time events from the Copilot session."""
    t = event.type
    d = event.data

    if t == SessionEventType.ASSISTANT_REASONING and d.content:
        console.print(f"[dim italic]{d.content}[/]")

    elif t == SessionEventType.TOOL_EXECUTION_START and d.tool_name:
        desc = ""
        if d.arguments:
            if d.tool_name == "bash" and d.arguments.get("command"):
                desc = f" [dim]{d.arguments['command']}[/]"
            elif d.tool_name == "report_intent":
                return  # skip noise
        console.print(f"[cyan]>>> {d.tool_name}[/]{desc}")

    elif t == SessionEventType.TOOL_EXECUTION_COMPLETE and d.result:
        content = getattr(d.result, "content", None)
        if content:
            console.print(f"[green]{content}[/]")

    elif t == SessionEventType.ASSISTANT_MESSAGE and d.content:
        console.print(d.content)


async def run_prompt(prompt: str, model_id: str, timeout: float = 3600) -> str:
    """Run a single prompt task with a fresh Copilot session.

    Creates a new client and session, subscribes to events for real-time
    output, sends the prompt, waits for completion, stops the client,
    and returns the final response content.
    """
    client = CopilotClient()
    await client.start()
    try:
        session = await client.create_session({
            "model": model_id,
            "tools": ALL_COPILOT_TOOLS,
            "on_permission_request": PermissionHandler.approve_all,
        })
        session.on(_event_handler)
        response = await session.send_and_wait({"prompt": _SYSTEM_PREFIX + prompt}, timeout=timeout)
        return response.data.content
    finally:
        await client.stop()
