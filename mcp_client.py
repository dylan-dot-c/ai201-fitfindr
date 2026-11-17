"""
Calling an MCP tool from your agent. ← UNIT 4

This is the plumbing, and it's given to you. Connecting over stdio and turning
the protocol's response back into a Python value is fiddly and it isn't the
lesson. What *is* the lesson is on the other side, in `mcp_server.py`: writing
a tool description and typed inputs that something other than your own code can
read.

Use it like this, in `run_agent()`:

    from mcp_client import call_tool

    results = call_tool("search_listings", {
        "description": "graphic tee",
        "max_price": 30,
    })

`results` comes back as the same list of dicts `search_listings` returned when
you called it directly. **That's the promise: the call changes shape, the
return value does not.** If it does change, that difference is information —
usually it means your tool was returning something you hadn't noticed.

Capstone change: by default the server is started ONCE and the session is
kept open on a background thread, instead of starting, asking and stopping it
on every call. On Render's free tier starting the server was ~8 s per search —
most of an agent run. Set AI201_MCP_PERSISTENT=0 to get the original
one-process-per-call behaviour back.
"""

import asyncio
import concurrent.futures
import json
import os
import sys
import threading
import time
from pathlib import Path

SERVER = Path(__file__).parent / "mcp_server.py"

PERSISTENT = os.getenv("AI201_MCP_PERSISTENT", "1") != "0"

# Counters, like generate.py's: serve.py diffs them around each request.
_mcp_calls = 0
_mcp_ms = 0.0


def stats() -> dict:
    """How many MCP calls this process has made, and the time spent in them."""
    return {"calls": _mcp_calls, "ms": round(_mcp_ms)}


class MCPError(RuntimeError):
    """The server couldn't be reached, or it refused the call."""


def call_tool(name: str, arguments: dict):
    """
    Call one tool on your MCP server and return what it returns.

    Args:
        name:      the tool name, exactly as registered in mcp_server.py.
        arguments: a dict of the tool's inputs. The names and types have to
                   match the registration — that's your Tool Inventory, now
                   being enforced by something other than you.

    Returns:
        Whatever the tool returns, unwrapped back to its native Python shape.
        A tool returning a list of dicts gives you a list of dicts.

    Raises:
        MCPError, with something readable in it.
    """
    global _mcp_calls, _mcp_ms
    started = time.perf_counter()
    try:
        if PERSISTENT:
            return _session.call(name, arguments)
        return asyncio.run(_call(name, arguments))
    except MCPError:
        raise
    except Exception as exc:  # noqa: BLE001 — re-raised readably below
        raise MCPError(
            f"Couldn't call '{name}' over MCP: {exc}\n"
            f"Check that mcp_server.py runs on its own first:\n"
            f"    python mcp_server.py\n"
            f"If it exits immediately with an error, fix that before coming back here."
        ) from exc
    finally:
        _mcp_calls += 1
        _mcp_ms += (time.perf_counter() - started) * 1000


class _PersistentSession:
    """
    One MCP server process and one open session, reused for every call.

    The session's async context managers have to be entered and left inside
    the same task, so a single long-lived task owns them, on an event loop
    running in its own daemon thread. call() hands it work through a queue and
    blocks on the answer. Because that loop is not the caller's thread,
    asyncio.run()'s "already running event loop" problem doesn't arise.

    If the server dies, the owning task ends; the next call starts a new one
    and retries once.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._loop = None
        self._queue = None
        self._task_done = None  # concurrent Future, set when the owner task ends

    def _ensure_loop(self):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, daemon=True,
                             name="mcp-session").start()

    def _start(self):
        """Start the server and wait until its session is ready (or failed)."""
        ready = concurrent.futures.Future()

        async def setup():
            self._queue = asyncio.Queue()
            return await self._own(ready)

        self._task_done = asyncio.run_coroutine_threadsafe(setup(), self._loop)
        ready.result(timeout=60)  # raises if the server couldn't start

    async def _own(self, ready):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    available = {t.name for t in (await session.list_tools()).tools}
                    ready.set_result(True)
                    while True:
                        name, arguments, answer = await self._queue.get()
                        if name is None:
                            return
                        if name not in available:
                            answer.set_exception(MCPError(
                                f"The server doesn't offer a tool called '{name}'.\n"
                                f"It offers: {', '.join(sorted(available)) or '(nothing yet)'}"
                            ))
                            continue
                        try:
                            result = await session.call_tool(name, arguments)
                        except Exception as exc:  # noqa: BLE001 — session is likely dead
                            answer.set_exception(exc)
                            raise
                        if getattr(result, "isError", False):
                            answer.set_exception(MCPError(
                                f"The tool '{name}' returned an error: {_text(result)}"))
                        else:
                            answer.set_result(_unwrap(result))
        except Exception as exc:  # noqa: BLE001
            if not ready.done():
                ready.set_exception(exc)
            raise

    def _alive(self) -> bool:
        return self._task_done is not None and not self._task_done.done()

    def _send(self, name: str, arguments: dict):
        answer = concurrent.futures.Future()
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (name, arguments, answer))
        return answer.result(timeout=120)

    def call(self, name: str, arguments: dict):
        with self._lock:
            self._ensure_loop()
            if not self._alive():
                self._start()
            try:
                return self._send(name, arguments)
            except MCPError:
                raise
            except Exception:  # noqa: BLE001 — server died mid-call: one fresh try
                if self._alive():
                    raise
                self._start()
                return self._send(name, arguments)


_session = _PersistentSession()


async def _call(name: str, arguments: dict):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            available = {t.name for t in (await session.list_tools()).tools}
            if name not in available:
                raise MCPError(
                    f"The server doesn't offer a tool called '{name}'.\n"
                    f"It offers: {', '.join(sorted(available)) or '(nothing yet)'}\n"
                    f"Register your tool in mcp_server.py — that's Milestone 1."
                )

            result = await session.call_tool(name, arguments)

            if getattr(result, "isError", False):
                raise MCPError(f"The tool '{name}' returned an error: {_text(result)}")

            return _unwrap(result)


def _unwrap(result):
    """
    Turn an MCP response back into the value the tool actually returned.

    MCP hands back content blocks rather than Python objects, so a tool that
    returned a list of dicts arrives as text containing JSON. This puts it
    back. Without this step your agent would start seeing strings where it used
    to see lists, and every downstream branch would quietly stop working.
    """
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        # FastMCP wraps a bare (non-dict) return value under "result".
        if set(structured) == {"result"}:
            return structured["result"]
        return structured

    text = _text(result)
    if text == "":
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _type_of(spec: dict) -> str:
    """Read a type out of a JSON schema entry, including optional ones."""
    if "type" in spec:
        return spec["type"]
    options = spec.get("anyOf") or spec.get("oneOf") or []
    names = [o.get("type") for o in options if o.get("type") and o.get("type") != "null"]
    return " or ".join(names) if names else "?"


def _text(result) -> str:
    parts = []
    for block in getattr(result, "content", []) or []:
        value = getattr(block, "text", None)
        if value:
            parts.append(value)
    return "\n".join(parts).strip()


# ── check it works ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Asking mcp_server.py what it offers…\n")

    async def _list():
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return (await session.list_tools()).tools

    try:
        tools = asyncio.run(_list())
    except Exception as exc:  # noqa: BLE001
        print(f"Couldn't reach the server: {exc}")
        sys.exit(1)

    if not tools:
        print("The server is running but offers no tools yet.")
        print("Register one in mcp_server.py — that's Milestone 1.")
        sys.exit(0)

    for tool in tools:
        print(f"  {tool.name}")
        print(f"    {tool.description or '(no description — write one)'}")
        schema = tool.inputSchema or {}
        required = set(schema.get("required", []))
        for key, spec in schema.get("properties", {}).items():
            kind = _type_of(spec)
            mark = "" if key in required else "  (optional)"
            print(f"    - {key}: {kind}{mark}")
        print()
