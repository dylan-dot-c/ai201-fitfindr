#!/usr/bin/env python3
"""
Send requests to the deployed FitFindr and write down what happened. ← CAPSTONE

    python run_live.py --label instrumentation         the default mix, once
    python run_live.py --label trial1                  same mix, a later trial
    python run_live.py --label cost --only ok -n 10    10 matching queries
    python run_live.py --label burst --parallel 3      3 requests at once
    python run_live.py --query 'denim jacket under $50' --query '{}'

`run_eval.py` runs the agent in this process. This runs it the way a user does:
over HTTP, against the Render URL, so the latency and the log are the deployed
system's, not your laptop's.

For every request it keeps two views of the same run:
  • what the caller saw — HTTP status, wall-clock time, the error message;
  • what the server logged — matched by the X-Request-Id header against
    GET /logs, so you can see whether every request left a record.

It writes both into results/live_<label>_<time>.md (a table plus the raw log
records, ready to paste) and a .jsonl with every row.

Like run_eval.py, it does NOT decide whether anything passed. Your criteria
say what passing is; this only produces the numbers they're checked against.

Uses only the standard library, so it runs without the project's venv.
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_URL = os.getenv("FITFINDR_URL", "https://fitfindr-8uv3.onrender.com")
RESULTS_DIR = Path(__file__).parent / "results"

# kind: what the request is meant to exercise. "ok" should find an item and
# write a fit card; the rest are the bad paths.
REQUESTS = [
    {"kind": "ok", "query": "vintage graphic tee under $30"},
    {"kind": "ok", "query": "denim jacket under $50"},
    {"kind": "ok", "query": "90s track jacket size M"},
    {"kind": "ok", "query": "silk slip dress under $40"},
    {"kind": "ok", "query": "platform sneakers size 8"},
    {"kind": "ok", "query": "cargo pants under $40"},
    {"kind": "ok", "query": "baggy jeans"},
    {"kind": "ok", "query": "leather bag"},
    {"kind": "ok", "query": "black jacket"},
    {"kind": "ok", "query": "white sneakers"},
    {"kind": "no_match", "query": "designer ballgown size XXS under $5"},
    {"kind": "bad_input", "body": "{}"},
    {"kind": "bad_input", "body": '{"query": "   "}'},
    {"kind": "bad_input", "body": "this is not json"},
]


def _http(method: str, url: str, body: str | None = None, timeout: float = 200.0):
    """One request. Returns (status, headers, text) — HTTP errors included."""
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode("utf-8", "replace")


def send(base: str, spec: dict) -> dict:
    """Send one /ask request and record what the caller saw."""
    body = spec.get("body")
    if body is None:
        body = json.dumps({"query": spec["query"]})
    row = {
        "kind": spec["kind"],
        "body": body,
        "sent_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds"),
    }
    started = time.perf_counter()
    try:
        status, headers, text = _http("POST", f"{base}/ask", body)
    except Exception as exc:  # noqa: BLE001 — a timeout or reset is a result too
        row.update(status=None, client_ms=round((time.perf_counter() - started) * 1000),
                   request_id=None, error=f"{type(exc).__name__}: {exc}")
        return row
    row["client_ms"] = round((time.perf_counter() - started) * 1000)
    row["status"] = status
    row["request_id"] = headers.get("X-Request-Id")
    try:
        payload = json.loads(text)
    except ValueError:
        payload = {"error": f"non-JSON response: {text[:200]}"}
    row["error"] = payload.get("error")
    item = payload.get("selected_item") or {}
    row["selected"] = item.get("title")
    row["fit_card"] = payload.get("fit_card")
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--label", default="live")
    ap.add_argument("--only", choices=["ok", "no_match", "bad_input"],
                    help="send only requests of this kind")
    ap.add_argument("-n", type=int, help="send this many (cycling through the list)")
    ap.add_argument("--query", action="append",
                    help="send this instead of the default mix; repeatable. "
                         "Anything starting with { is sent as the raw body")
    ap.add_argument("--parallel", type=int, default=1,
                    help="how many requests in flight at once (default 1)")
    args = ap.parse_args()
    base = args.url.rstrip("/")

    if args.query:
        specs = [
            {"kind": "custom", "body": q} if q.lstrip().startswith("{")
            else {"kind": "custom", "query": q}
            for q in args.query
        ]
    else:
        specs = [s for s in REQUESTS if not args.only or s["kind"] == args.only]
    if args.n:
        specs = [specs[i % len(specs)] for i in range(args.n)]

    # Wake it first and time that separately, so a cold start doesn't hide
    # inside the first /ask's latency.
    t0 = time.perf_counter()
    try:
        status, _, _ = _http("GET", f"{base}/health", timeout=180)
    except Exception as exc:  # noqa: BLE001
        print(f"{base}/health did not answer: {exc}", file=sys.stderr)
        return 1
    health_ms = round((time.perf_counter() - t0) * 1000)
    print(f"/health {status} in {health_ms} ms "
          f"({'cold start' if health_ms > 5000 else 'warm'})")

    print(f"sending {len(specs)} request(s), {args.parallel} at a time ...")
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        rows = []
        for row in pool.map(lambda s: send(base, s), specs):
            rows.append(row)
            print(f"  {row['status']}  {row['client_ms']:>6} ms  {row['kind']:<9} {row['body'][:50]}")

    # Match each request to its server record.
    # If the instance restarted mid-run, /logs may be a 502 page or an empty
    # list. That's a result, not a reason to lose the client-side rows.
    try:
        status, _, text = _http("GET", f"{base}/logs?n=200")
        server = {r.get("request_id"): r for r in json.loads(text)}
    except Exception as exc:  # noqa: BLE001
        print(f"  could not read /logs ({exc}); every row will say NOT LOGGED",
              file=sys.stderr)
        server = {}
    for row in rows:
        row["server"] = server.get(row["request_id"])

    write(args, base, health_ms, rows)
    return 0


def _avg(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return round(sum(values) / len(values), 1) if values else None


def write(args, base: str, health_ms: int, rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    stem = RESULTS_DIR / f"live_{args.label}_{stamp}"

    with open(f"{stem}.jsonl", "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    logged = [r for r in rows if r["server"]]
    ok = [r["server"] for r in logged if r["server"].get("outcome") == "ok"]
    lines = [
        f"# Live run — {args.label}",
        "",
        f"- URL: {base}",
        f"- When: {rows[0]['sent_at'] if rows else '-'} (UTC)",
        f"- `/health` before the run: {health_ms} ms",
        f"- Requests: {len(rows)}, {args.parallel} at a time",
        f"- With a matching server log record: {len(logged)} of {len(rows)}",
        f"- Server boot ids seen (more than one = it restarted): "
        f"{sorted({r['server'].get('boot_id') for r in logged}) or '-'}",
        "",
        "| # | kind | request body | HTTP | client ms | server outcome | server ms | queue ms | calls | tokens in/out | rss MB | child peak MB |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        s = r["server"] or {}
        body = r["body"].replace("|", "\\|")
        tokens = (f"{s['prompt_tokens']}/{s['output_tokens']}"
                  if "prompt_tokens" in s else "-")
        lines.append(
            f"| {i} | {r['kind']} | `{body}` | {r['status']} | {r['client_ms']} | "
            f"{s.get('outcome', 'NOT LOGGED')} | {s.get('duration_ms', '-')} | "
            f"{s.get('queue_wait_ms', '-')} | {s.get('model_calls', '-')} | {tokens} | "
            f"{s.get('rss_mb', '-')} | {s.get('child_peak_rss_mb', '-')} |"
        )
    lines += [
        "",
        "## Averages over requests with outcome `ok`",
        "",
        f"- Runs: {len(ok)}",
        f"- Model calls: {_avg([s.get('model_calls') for s in ok])}",
        f"- Prompt tokens: {_avg([s.get('prompt_tokens') for s in ok])}",
        f"- Output tokens: {_avg([s.get('output_tokens') for s in ok])}",
        f"- Server duration ms: {_avg([s.get('duration_ms') for s in ok])}",
        "",
        "## Server log records (from GET /logs, written by serve.py::_log)",
        "",
        "```",
        *[json.dumps(r["server"], ensure_ascii=False) for r in logged],
        "```",
    ]
    errors = [r for r in rows if r["error"]]
    if errors:
        lines += ["", "## Errors the caller saw", ""]
        lines += [f"- `{r['body'][:60]}` → {r['status']}: {r['error']}" for r in errors]

    Path(f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {stem}.md and .jsonl")


if __name__ == "__main__":
    sys.exit(main())
