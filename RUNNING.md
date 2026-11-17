# Running FitFindr

Everything about how the starter works and how to use it.

---

## Try the live one first (nothing to install)

FitFindr runs at **https://fitfindr-8uv3.onrender.com**. You type what
secondhand item you want; it finds a matching listing and writes an outfit
suggestion and a short caption ("fit card"). There's no web page; you talk to
it with one command.

**1. Wake it up.** It sleeps when nobody's used it for ~15 minutes; the first
call can take up to a minute.

```bash
curl https://fitfindr-8uv3.onrender.com/health        # {"status":"ok"} means ready
```

**2. Ask for something.** Change the text in `"query"`.

macOS / Linux / Git Bash:

```bash
curl -X POST https://fitfindr-8uv3.onrender.com/ask \
  -H 'Content-Type: application/json' \
  -d '{"query": "vintage graphic tee under $30"}'
```

Windows PowerShell (keep the single quotes, or `$30` disappears):

```powershell
$r = Invoke-RestMethod 'https://fitfindr-8uv3.onrender.com/ask' -Method Post `
     -ContentType 'application/json' -Body '{"query": "vintage graphic tee under $30"}'
$r.error; $r.selected_item.title; $r.outfit_suggestion; $r.fit_card
```

**3. Read the answer.** Check `error` first: if it isn't `null`, it says why
nothing came back and what to change. Otherwise look at `selected_item`,
`outfit_suggestion` and `fit_card`.

**4. See what the server recorded:**
`https://fitfindr-8uv3.onrender.com/logs?n=5` (opens in a browser).

Things to know: it answers one request at a time, so a second one waits its
turn; and it's on Gemini's free tier (15 model calls a minute, two per
request), so if lots of people ask at once, some answers take a minute or
more.

Ideas: `denim jacket size S`, `cargo pants under $40`, `black jacket`,
`leather bag`. Size and price are optional.

---

## Before your first class

Setup happens **before class**. The [environment setup page](../pages/ide_setup)
has the per-operating-system commands and the exact versions.

**Same API key you set up in unit 1.** Nothing new to sign up for. There is one
new package — the MCP SDK, for unit 4 — and it installs with everything else.

From inside this repo after you've forked and cloned it:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your key into .env
python test.py
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env         # then paste your key into .env
python test.py
```

**You're ready when `python test.py` passes.**

If it doesn't and you've made one honest attempt at the error, post the
**whole** output in the help channel.

> Activate the virtual environment every time you open a new terminal. You
> should see `(.venv)` at the start of your prompt.

---

## Your first five minutes

Start with the data. Your tools will only be as good as your understanding of
what they're reading, and ten minutes here saves an hour of confused debugging.

```bash
python app.py fields                    # what a listing and a wardrobe item hold
python app.py listings --full -n 6      # read six listings all the way through
python app.py examples                  # queries worth trying
python app.py ask 'vintage graphic tee under $30'
```

> **Quote your queries with single quotes**, on every operating system. In
> PowerShell, `"vintage graphic tee under $30"` in double quotes silently
> becomes `vintage graphic tee under ` — PowerShell reads `$30` as a variable
> and substitutes nothing. You get results with no price ceiling and no error
> saying so. Single quotes are literal in PowerShell, bash and zsh alike.

That last one runs the loop. All three tools are stubs, so it will tell you the
loop isn't built yet. **That's the correct starting position** — it runs, and it
does nothing.

---

## Every command

| Command | What it does |
|---|---|
| `python test.py` | Checks your environment. Run it whenever something feels off |
| `python app.py fields` | The fields a listing and a wardrobe item have — **Milestone 1** |
| `python app.py listings` | Browse the data. `--full` for whole records, `-n` for how many |
| `python app.py examples` | Queries worth trying, including one that matches nothing |
| `python app.py ask '...'` | Run the agent on one query — **single quotes** |
| `python app.py ask` | Keep asking until you press Enter on an empty line |
| `python agent.py` | Runs both example paths — one that matches, one that can't |
| `python mcp_server.py` | Starts your MCP server — **unit 4** |
| `python mcp_client.py` | Asks the server what it offers — **unit 4** |
| `python run_eval.py --label before` | Runs every scenario five times and writes the run log — **unit 4** |
| `python serve.py` | Serves the agent over HTTP instead of exiting — **unit 9** |
| `python run_live.py --label X` | Sends a mix of good and bad requests to the deployed URL, matches each to its server log record, and writes `results/live_X_*.md` — **capstone**. `--only ok -n 10`, `--parallel 3`, `--query '...'`, `--url` |

Useful flags on `ask`:

| Flag | What it does |
|---|---|
| `--trace` | Print the loop step by step, once you've added the trace calls |
| `--empty-wardrobe` | Run as a user with nothing saved — one of unit 4's failure modes |

---

## Which command goes with which milestone

### Unit 3 — the build

| Milestone | What you're doing | Where |
|---|---|---|
| 1 | Read the data, run the starter | `app.py fields`, `app.py listings --full`, `app.py ask` |
| 2 | Spec your three tools | README, **Tool Inventory** |
| 3 | Write your acceptance criteria | `criteria.md` |
| 4 | Build the three tools | `tools.py`, tested one at a time from a terminal |
| 5 | Wire the loop and the state | `agent.py::run_agent` |
| 6 | Write it up | README |

### Unit 4 — the test

| Milestone | What you're doing | Where |
|---|---|---|
| 1 | Move one tool onto MCP | `mcp_server.py`, then `mcp_client.call_tool` in `run_agent` |
| 2 | Break it on purpose, then trace it | `trace.py`, `app.py ask --trace` |
| 3 | Run your test | `scenarios.py`, then `run_eval.py --label before` |
| 4 | Call each criterion, diagnose the misses | README |
| 5 | Fix one thing and re-run | `run_eval.py --label after` |
| 6 | Say what's still broken | README |

---

## Running it somewhere else — **unit 9**

Everything above exits when the command finishes. A host has nothing to keep
running, so before you can deploy this you need something that stays up.
`serve.py` is that: the same `run_agent()`, behind two HTTP routes.

On your machine:

```bash
python serve.py
curl -X POST http://localhost:5000/ask \
  -H 'Content-Type: application/json' \
  -d '{"query": "vintage graphic tee under $30"}'
```

On a host, the start command is:

```bash
gunicorn serve:app
```

| Thing | What it means |
|---|---|
| `PORT` | The host tells your app which port to listen on by setting this. Both `serve.py` and `gunicorn` read it, and `serve.py` falls back to `5000` on your machine. Don't hard-code a port |
| `POST /ask` | `{"query": "...", "wardrobe": {...}}` — wardrobe optional. Returns the session dict, `error` and all |
| `GET /health` | Says `ok` if the app is awake |
| It answers one request at a time | On purpose. A second request waits for the first to finish, and prints `[serve] another request is still running` while it waits. An MCP tool call starts a whole second Python process, and the free tier's 512 MB has no room for two of those at once — and `generate.py`'s rate-limit counting assumes one caller. The reasoning is written out in `serve.py` |
| `gunicorn serve:app`, exactly | Not `-k gevent`, not `-k eventlet`, not wrapped for uvicorn. `mcp_client.call_tool` uses `asyncio.run()`, which won't start inside a running event loop, so an async worker breaks **every** MCP call — and only once you've deployed it |
| The first request is slow | The free tier puts your app to sleep after about fifteen minutes of nothing. The next request wakes it up and waits for it — around a minute. Not a bug, and worth knowing before you demo it |

### Deployed on Render (capstone)

The service is defined in [render.yaml](render.yaml), so there's nothing to
type into Render's settings except the key.

1. Push this repo to GitHub.
2. On [render.com](https://render.com): **New → Blueprint**, connect GitHub,
   pick this repo. Render reads `render.yaml` and creates a free web service
   called `fitfindr`.
3. When it asks for `GEMINI_API_KEY`, paste your key. It's stored by Render,
   not in the repo.
4. Wait for the build to finish and the health check on `/health` to pass. The
   URL is at the top of the service page, `https://fitfindr-XXXX.onrender.com`.

What `render.yaml` sets, and why:

| Setting | Why |
|---|---|
| `gunicorn serve:app --workers 1 --threads 4 --timeout 180` | One process, so `serve.py`'s lock covers every request. Threads (not an async worker), so MCP's `asyncio.run()` still works **and `/health` answers during an agent run** — without them Render's health check timed out mid-run and restarted the instance. 180s because one run is several model calls and the limiter can wait up to 65s; gunicorn's default 30s kills those runs |
| `PYTHON_VERSION=3.13.5` | `requirements.txt` supports 3.11–3.13; Render's default can be newer |
| `AI201_CACHE=0` | Every request makes real model calls, so the token counts in the log are what a run actually costs |

Try it (the first request after ~15 minutes idle takes about a minute while it wakes):

```bash
curl https://fitfindr-XXXX.onrender.com/health
curl -X POST https://fitfindr-XXXX.onrender.com/ask \
  -H 'Content-Type: application/json' \
  -d '{"query": "vintage graphic tee under $30"}'
curl 'https://fitfindr-XXXX.onrender.com/logs?n=20'
```

### The request log

Every `/ask` request writes one JSON record: answered, rejected (400) and
crashed (500) alike. Each record goes to stdout, where Render's **Logs** tab
keeps it, and to `logs/requests.jsonl`, which `GET /logs?n=20` (max 200)
reads back.

The free instance **wipes its disk when it sleeps**, so `/logs` only holds what
happened since it last woke. Copy what you need into the README the same
session.

| Field | What it is |
|---|---|
| `ts` | UTC timestamp when the request arrived |
| `request_id` | 8 random hex characters, to find one request among many |
| `model`, `cache_enabled` | Which model answered, and whether cached answers were allowed |
| `query`, `wardrobe_items` | What came in |
| `status` | HTTP status returned: 200, 400 or 500 |
| `outcome` | `ok` (fit card written), `no_results`, `model_error` (found an item, model failed), `rejected` (bad request), `crash` (exception) |
| `error` | `session["error"]`, or the exception, or `null` |
| `parsed`, `results`, `selected_id`, `selected_price`, `fit_card_chars` | What came out |
| `model_calls`, `prompt_tokens`, `output_tokens` | This request's spend, as reported by Gemini |
| `queue_wait_ms`, `agent_ms`, `duration_ms` | Time waiting for the lock, time in `run_agent()`, total |
| `mcp_calls`, `mcp_ms`, `mcp_persistent` | MCP searches this request made, the time spent in them, and whether the MCP server was kept running between calls |
| `boot_id`, `uptime_s` | Changes on every process start; a different `boot_id` between two records means the instance restarted |
| `rss_mb`, `peak_rss_mb`, `child_peak_rss_mb` | Memory in MB (Linux only). The free tier's limit is 512 |

### The MCP server stays running (capstone improvement)

`mcp_client.call_tool` used to start `mcp_server.py`, make one call and stop
it, every time. On Render's free tier that cost about 8 s per search. It now
starts the server once per process and keeps the session open on a background
thread; if the server dies, the next call starts a new one. Set
`AI201_MCP_PERSISTENT=0` (in `.env`, or in Render's environment) to get the
old one-process-per-call behaviour back.

---

## Where everything lives

| File | What it does |
|---|---|
| `config.py` | Every setting worth changing — **TEMPERATURE and the cache are at the top** |
| `tools.py` | Your three tools. **Stubs — you build these** |
| `agent.py` | The planning loop and the session. **Stub — you build this** |
| `generate.py` | The only thing that calls out to a service. Handles pacing and quota |
| `trace.py` | The trace helper, and the loop's stop condition |
| `app.py` | The command line |
| `serve.py` | The same agent over HTTP, for deploying — **unit 9** |
| `mcp_server.py` | Your MCP server — **unit 4, you register the tool** |
| `mcp_client.py` | Calling an MCP tool from your agent. Given to you |
| `scenarios.py` | What your test runs. **You fill this in** |
| `run_eval.py` | Runs the scenarios repeatedly and writes the run log |
| `criteria.md` | Your five acceptance criteria. **You fill this in** |
| `data/` | 40 listings and the wardrobe schema |
| `utils/data_loader.py` | Loading the data. Use this rather than reading the files yourself |
| `results/` | Run logs. **Commit these** — they're your evidence |

---

## The two settings people go looking for

Both are at the top of `config.py`, and the brief points at them by name.

If your fit cards come out **word-for-word identical** every time, it is one of:

- **`CACHE_ENABLED`** — while you build, identical prompts reuse the answer
  already received. That's deliberate; it makes debugging free. `run_eval.py`
  turns it off automatically.
- **`TEMPERATURE`** — at `0.0` the model gives you the same words every time.
  It ships at `0.9`.

---

## About rate limits

**This is the heaviest pair in the course for call volume.** Two of your three
tools call the model, so one agent run is several requests, and a few runs back
to back while debugging can cross the per-minute limit.

`generate.py` handles it:

- **It paces itself** and says when it's waiting. **A pause is the starter
  doing its job, not a bug.**
- **It reuses answers** to prompts already sent, while you build.
- **It stops** if a session makes an unreasonable number of calls, rather than
  draining your day's allowance. For an agent, that usually means a loop isn't
  ending — look for that before raising the number.
- **It counts your calls** and prints the total when you exit.

`config.MAX_ITERATIONS` is the loop's own stop condition. Your loop this unit
is short enough that you may never hit it. Keep it — a missing stop condition
is the most common architectural failure in production agents.

---

## When something goes wrong

| What you see | What it means |
|---|---|
| `The planning loop isn't built yet` | Correct, at the start. That's the TODO in `agent.py` |
| `No GEMINI_API_KEY found` | No `.env`, or the key wasn't pasted in. On Windows check it didn't save as `.env.txt` |
| A message saying the model couldn't be reached | Usually a bad key. This is also **exactly what unit 4 Milestone 2 asks you to trigger on purpose** |
| `[rate limit] ... Waiting 34s` | Working as intended. Leave it |
| `[serve] another request is still running` | Also working as intended. `serve.py` answers one request at a time; yours is queued behind one that's mid-run |
| `QuotaGuard: This session has made 300 requests` | A loop isn't ending. Find it before raising the budget |
| `The loop ran 11 times, past MAX_ITERATIONS` | Same thing, caught earlier |
| `The server doesn't offer a tool called '...'` | Nothing registered in `mcp_server.py` yet, or the name doesn't match |
| MCP returns a string where you expected a list | You're not going through `mcp_client.call_tool`, which unwraps it |
| Fit cards identical every run | `CACHE_ENABLED` or `TEMPERATURE`. See above |
| `--trace` prints nothing | You haven't added `trace.step()` calls yet — unit 4, Milestone 2 |
| `IncompleteFieldDefinitionWarning: Field 'lifespan'` | Harmless noise from the MCP library's dependencies. Not your code, not an error. Ignore it |
| A price ceiling you typed is being ignored | You used double quotes in PowerShell. `$30` vanished. Use single quotes |
| `UnicodeEncodeError: 'charmap' codec can't encode` | Shouldn't happen — `config.py` sets the console to UTF-8. If you see it, you're running a file that doesn't import `config` |

Still stuck after one honest attempt? Post in the help channel with the full
error, what you ran, and what you expected.

---

## A note on committing

At least four new commits in unit 3, at least four more in unit 4. Your commit
history is what shows your criteria existed before your results did.

**Do not delete and recreate this repository.** You submit the same URL both
units.

`results/` is deliberately **not** in `.gitignore`.
