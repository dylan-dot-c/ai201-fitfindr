#!/usr/bin/env python3
"""
FitFindr over HTTP. ← UNIT 9

    python serve.py                       run it on your machine
    gunicorn serve:app                    run it the way a host runs it

Everything else in this repo exits after one command. A host has nothing to
keep running, so a command line cannot be deployed. This file is the smallest
thing that can: it starts a web server, waits, and hands each request to the
same `run_agent()` your CLI calls. **No new agent logic lives here.** If your
loop works from `python app.py ask`, it works from here; if it doesn't, fix it
there, not in this file.

Two routes:

    POST /ask       {"query": "vintage graphic tee under $30",
                     "wardrobe": {...}}     ← wardrobe is optional
    GET  /health    is it awake?

`/ask` returns the session dict from `run_agent()` as JSON, unchanged — the
same keys you print from the command line, including `error`. Read
`session["error"]` first, exactly as you do everywhere else.

It runs **one request at a time**, and one route is deliberately slower than a
web server has to be. The reason is worth reading before you deploy: see the
note above `_one_at_a_time` below — it also decides which gunicorn worker you
can use.

Instrumentation (capstone): every /ask request — answered, rejected or
crashed — writes one JSON record to stdout (where Render's log viewer keeps
it) and to logs/requests.jsonl. `GET /logs?n=20` reads the file back, because
a free Render instance wipes its disk when it sleeps.
"""

import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

# config first, and before anything that talks to the model: it loads your .env
# and fixes the Windows console encoding for every module that imports it.
import config  # noqa: F401

from flask import Flask, g, jsonify, request

import generate
from agent import run_agent
from utils.data_loader import get_example_wardrobe

app = Flask(__name__)

LOG_FILE = config.ROOT / "logs" / "requests.jsonl"


@app.after_request
def _tag_response(response):
    """Echo the log record's id back, so a caller can find its own record."""
    if "request_id" in g:
        response.headers["X-Request-Id"] = g.request_id
    return response


# Changes every time the process starts. Two records with different boot ids
# had a restart between them — which on Render also means the log file and
# everything before it is gone.
BOOT_ID = uuid.uuid4().hex[:6]
BOOTED = time.monotonic()


def _memory() -> dict:
    """
    Memory in MB, because the free tier kills the whole instance at 512.

    rss_mb is this process now; peak_rss_mb its high-water mark;
    child_peak_rss_mb the largest finished child (the MCP server processes).
    Linux only — on Windows these come out None.
    """
    mem = {"rss_mb": None, "peak_rss_mb": None, "child_peak_rss_mb": None}
    try:
        import resource  # not on Windows

        # ru_maxrss is in KB on Linux.
        mem["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
        mem["child_peak_rss_mb"] = round(
            resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1)
        with open("/proc/self/status", encoding="ascii") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    mem["rss_mb"] = round(int(line.split()[1]) / 1024, 1)
    except (ImportError, OSError, ValueError):
        pass
    return mem


def _log(record: dict) -> None:
    """Write one structured record: a line of JSON to stdout and to LOG_FILE."""
    record["boot_id"] = BOOT_ID
    record["uptime_s"] = round(time.monotonic() - BOOTED)
    record.update(_memory())
    line = json.dumps(record, ensure_ascii=False, default=str)
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as exc:  # a full or read-only disk must not fail the request
        print(f"  [serve] could not write {LOG_FILE}: {exc}", file=sys.stderr, flush=True)


def _outcome(session: dict) -> str:
    """Which way the run ended, as one word you can count."""
    if session.get("fit_card"):
        return "ok"
    if not session.get("search_results"):
        return "no_results"
    return "model_error"


# ── one request at a time ─────────────────────────────────────────────────────
# Here's why this exists.
#
# A web server will happily run two requests at once. Two things in this repo
# assume otherwise:
#
#   • If you moved a tool onto MCP in unit 4, `mcp_client.call_tool` starts
#     `mcp_server.py` as a separate process over stdio, one per call. Two
#     overlapping requests means two extra Python interpreters, and the free
#     tier you're deploying to has 512 MB for all of it. That is the reason
#     that would still be here even if everything else were perfect.
#   • `generate.py`'s pacing window and its call counter are plain module
#     globals — deliberately, because that file is teaching pacing and quota,
#     not locking. Two threads sharing them means the per-minute limiter is
#     counting something that isn't true.
#
# What the lock covers is exactly the agent run: the part that spawns
# processes and calls the model. Reading the request, rejecting a bad one, and
# turning the answer into JSON all happen outside it — so a request with a
# malformed body comes straight back with a 400 instead of queueing behind
# somebody else's agent.
#
# Serialising the runs costs you nothing here — this is one user asking one
# question — and it keeps the deployed behaviour identical to the CLI's. When
# that stops being an acceptable trade, the fix is a real queue, not a bigger
# lock.
#
# The same constraint decides your start command, and this is the part that
# bites in deployment rather than on your machine. `mcp_client.call_tool`
# wraps `asyncio.run()`, and `asyncio.run()` refuses to start when an event
# loop is already running. An async worker always has one running. So under
# `gunicorn -k gevent` (or `-k eventlet`, or `serve:app` wrapped for an ASGI
# server like uvicorn) EVERY MCP call fails with "asyncio.run() cannot be
# called from a running event loop" — not some of them under load, all of
# them, every time, in a place your laptop never showed you.
#
#     gunicorn serve:app              ← right: the DEFAULT sync worker
#     gunicorn -k gevent serve:app    ← breaks every MCP call you make
#
# On Render this repo runs `--threads 4` (see render.yaml): still no event
# loop, so MCP works, but /health gets a thread while an agent run is busy.

_one_at_a_time = threading.Lock()


@app.get("/health")
def health():
    """Is the server awake? A host pings something like this to find out."""
    return jsonify({"status": "ok"})


@app.post("/ask")
def ask():
    """
    Run the agent on one query.

    In:   {"query": "...", "wardrobe": {...}}   wardrobe optional — leave it
                                                out and you get the same
                                                example wardrobe the CLI uses.
    Out:  the session dict from run_agent(), as JSON.
    """
    started = time.perf_counter()
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "request_id": uuid.uuid4().hex[:8],
        "model": config.MODEL,
        "cache_enabled": config.CACHE_ENABLED,
    }
    g.request_id = record["request_id"]
    # stdout only: if the instance dies mid-run, this line in Render's log is
    # the only sign the request ever arrived.
    print(json.dumps({"event": "start", "ts": record["ts"],
                      "request_id": record["request_id"], "boot_id": BOOT_ID}),
          flush=True)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    query = payload.get("query")
    query = query.strip() if isinstance(query, str) else ""
    if not query:
        # 400 rather than a stack trace: the caller can act on this one.
        record.update({
            "query": None,
            "status": 400,
            "outcome": "rejected",
            "error": "missing 'query'",
            "duration_ms": round((time.perf_counter() - started) * 1000),
        })
        _log(record)
        return jsonify({"error": "Send JSON with a 'query' field, e.g. "
                                 '{"query": "vintage graphic tee under $30"}'}), 400

    wardrobe = payload.get("wardrobe")
    if not isinstance(wardrobe, dict):
        wardrobe = get_example_wardrobe()

    # A queued request should look like a queued request. Without this the
    # second caller just sits there, and "slow" and "waiting its turn" are
    # indistinguishable from the outside — which is how people conclude the
    # deployment is broken when it is behaving exactly as designed.
    #
    # This is NOT the logging you add in the follow-along. It prints nothing
    # on the normal path, carries no timing and counts nothing; it says only
    # that this request had to wait. `locked()` can be a moment out of date,
    # so the note is occasionally missed — which costs nothing, because
    # nothing depends on it.
    if _one_at_a_time.locked():
        print(
            "  [serve] another request is still running. This one is waiting "
            "its turn — serve.py handles one at a time, on purpose.",
            file=sys.stderr,
            flush=True,
        )

    record["query"] = query
    record["wardrobe_items"] = len(wardrobe.get("items") or [])

    failure = None
    session = None
    with _one_at_a_time:
        # Inside the lock nobody else is calling the model, so the difference
        # in generate.py's session counters is exactly this request's spend.
        lock_acquired = time.perf_counter()
        calls_before = generate.call_count()
        tokens_before = generate.token_counts()
        try:
            session = run_agent(query, wardrobe)
        except Exception as exc:  # noqa: BLE001 — a 500 with a sentence beats a hang
            failure = f"{type(exc).__name__}: {exc}"
        finished = time.perf_counter()
        tokens_after = generate.token_counts()
        record["model_calls"] = generate.call_count() - calls_before
        record["prompt_tokens"] = tokens_after["prompt"] - tokens_before["prompt"]
        record["output_tokens"] = tokens_after["output"] - tokens_before["output"]

    # Outside the lock: building a response is not work the next caller should
    # be waiting on.
    record["queue_wait_ms"] = round((lock_acquired - started) * 1000)
    record["agent_ms"] = round((finished - lock_acquired) * 1000)

    if failure is not None:
        record.update({"status": 500, "outcome": "crash", "error": failure})
        record["duration_ms"] = round((time.perf_counter() - started) * 1000)
        _log(record)
        return jsonify({"error": failure}), 500

    item = session.get("selected_item") or {}
    record.update({
        "status": 200,
        "outcome": _outcome(session),
        "error": session.get("error"),
        "parsed": session.get("parsed"),
        "results": len(session.get("search_results") or []),
        "selected_id": item.get("id"),
        "selected_price": item.get("price"),
        "fit_card_chars": len(session.get("fit_card") or ""),
    })
    record["duration_ms"] = round((time.perf_counter() - started) * 1000)
    _log(record)
    return jsonify(session)


@app.get("/logs")
def logs():
    """
    The last n log records (default 20, max 200), oldest first.

    Here because a free Render instance loses its disk when it sleeps: copy
    these into the README the same session you produce them.
    """
    try:
        n = max(1, min(200, int(request.args.get("n", 20))))
    except ValueError:
        n = 20
    if not LOG_FILE.exists():
        return jsonify([])
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()[-n:]
    return jsonify([json.loads(line) for line in lines if line.strip()])


if __name__ == "__main__":
    # PORT and 0.0.0.0 are not decoration. A host tells you which port to
    # listen on through PORT, and it reaches your process from outside the
    # container — bind 127.0.0.1 and nothing but the container itself can
    # connect, which looks exactly like a broken app from the browser.
    port = int(os.getenv("PORT", "5000"))

    # Never on by default. Flask's debugger executes code typed into a browser,
    # and a deployed app with it on is a stranger's shell. Set AI201_DEBUG=1 in
    # your own terminal when you want the reloader.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"\nFitFindr is listening on http://localhost:{port}")
    print("It runs one request at a time — a second one waits for the first.")
    print("Ask it something (single quotes, as always):\n")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"query\": \"vintage graphic tee under $30\"}}'\n"
    )
    print("Ctrl-C to stop.\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
