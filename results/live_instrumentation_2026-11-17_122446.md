# Live run — instrumentation

- URL: https://fitfindr-8uv3.onrender.com
- When: 2026-11-17T17:20:46.975+00:00 (UTC)
- `/health` before the run: 163 ms
- Requests: 14, 1 at a time
- With a matching server log record: 14 of 14
- Server boot ids seen (more than one = it restarted): ['c7da3a']

| # | kind | request body | HTTP | client ms | server outcome | server ms | queue ms | calls | tokens in/out | rss MB | child peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ok | `{"query": "vintage graphic tee under $30"}` | 200 | 6903 | ok | 6584 | 0 | 2 | 589/161 | 100.7 | 100.1 |
| 2 | ok | `{"query": "denim jacket under $50"}` | 200 | 11046 | ok | 10913 | 0 | 2 | 566/135 | 100.7 | 100.1 |
| 3 | ok | `{"query": "90s track jacket size M"}` | 200 | 13050 | ok | 12903 | 1 | 3 | 605/178 | 100.7 | 100.1 |
| 4 | ok | `{"query": "silk slip dress under $40"}` | 200 | 16997 | ok | 16839 | 0 | 2 | 614/159 | 100.7 | 100.1 |
| 5 | ok | `{"query": "platform sneakers size 8"}` | 200 | 15956 | ok | 15805 | 0 | 2 | 554/121 | 100.7 | 100.1 |
| 6 | ok | `{"query": "cargo pants under $40"}` | 200 | 17648 | ok | 17497 | 0 | 2 | 625/188 | 100.7 | 100.1 |
| 7 | ok | `{"query": "baggy jeans"}` | 200 | 32233 | ok | 31926 | 0 | 2 | 607/172 | 100.7 | 100.1 |
| 8 | ok | `{"query": "leather bag"}` | 200 | 16522 | ok | 16341 | 0 | 2 | 596/171 | 100.8 | 100.2 |
| 9 | ok | `{"query": "black jacket"}` | 200 | 77540 | ok | 77373 | 0 | 3 | 610/187 | 100.8 | 100.2 |
| 10 | ok | `{"query": "white sneakers"}` | 200 | 17313 | ok | 17161 | 2 | 2 | 567/124 | 100.8 | 100.2 |
| 11 | no_match | `{"query": "designer ballgown size XXS under $5"}` | 200 | 13200 | no_results | 12914 | 0 | 0 | 0/0 | 100.8 | 100.3 |
| 12 | bad_input | `{}` | 400 | 152 | rejected | 0 | - | - | - | 100.8 | 100.3 |
| 13 | bad_input | `{"query": "   "}` | 400 | 138 | rejected | 0 | - | - | - | 100.8 | 100.3 |
| 14 | bad_input | `this is not json` | 400 | 193 | rejected | 0 | - | - | - | 100.8 | 100.3 |

## Averages over requests with outcome `ok`

- Runs: 10
- Model calls: 2.2
- Prompt tokens: 593.3
- Output tokens: 159.6
- Server duration ms: 22334.2

## Server log records (from GET /logs, written by serve.py::_log)

```
{"agent_ms": 6584, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 6584, "error": null, "fit_card_chars": 256, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 161, "parsed": {"description": "vintage graphic tee", "max_price": 30.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 589, "query": "vintage graphic tee under $30", "queue_wait_ms": 0, "request_id": "fad636d6", "results": 10, "rss_mb": 100.7, "selected_id": "lst_002", "selected_price": 18.0, "status": 200, "ts": "2026-11-17T17:20:49.025+00:00", "uptime_s": 477, "wardrobe_items": 10}
{"agent_ms": 10913, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 10913, "error": null, "fit_card_chars": 218, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 135, "parsed": {"description": "denim jacket", "max_price": 50.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 566, "query": "denim jacket under $50", "queue_wait_ms": 0, "request_id": "b682eae9", "results": 7, "rss_mb": 100.7, "selected_id": "lst_007", "selected_price": 42.0, "status": 200, "ts": "2026-11-17T17:20:55.926+00:00", "uptime_s": 488, "wardrobe_items": 10}
{"agent_ms": 12902, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 12903, "error": null, "fit_card_chars": 276, "model": "gemini-3.5-flash-lite", "model_calls": 3, "outcome": "ok", "output_tokens": 178, "parsed": {"description": "90s track jacket", "max_price": null, "size": "M"}, "peak_rss_mb": 100.1, "prompt_tokens": 605, "query": "90s track jacket size M", "queue_wait_ms": 1, "request_id": "934a1612", "results": 5, "rss_mb": 100.7, "selected_id": "lst_004", "selected_price": 45.0, "status": 200, "ts": "2026-11-17T17:21:06.987+00:00", "uptime_s": 501, "wardrobe_items": 10}
{"agent_ms": 16839, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 16839, "error": null, "fit_card_chars": 187, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 159, "parsed": {"description": "silk slip dress", "max_price": 40.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 614, "query": "silk slip dress under $40", "queue_wait_ms": 0, "request_id": "76ebec83", "results": 2, "rss_mb": 100.7, "selected_id": "lst_013", "selected_price": 30.0, "status": 200, "ts": "2026-11-17T17:21:20.048+00:00", "uptime_s": 518, "wardrobe_items": 10}
{"agent_ms": 15805, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 15805, "error": null, "fit_card_chars": 216, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 121, "parsed": {"description": "platform sneakers", "max_price": null, "size": "8"}, "peak_rss_mb": 100.1, "prompt_tokens": 554, "query": "platform sneakers size 8", "queue_wait_ms": 0, "request_id": "061f4f10", "results": 1, "rss_mb": 100.7, "selected_id": "lst_019", "selected_price": 48.0, "status": 200, "ts": "2026-11-17T17:21:37.038+00:00", "uptime_s": 534, "wardrobe_items": 10}
{"agent_ms": 17497, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 17497, "error": null, "fit_card_chars": 211, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 188, "parsed": {"description": "cargo pants", "max_price": 40.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 625, "query": "cargo pants under $40", "queue_wait_ms": 0, "request_id": "2f4daa7e", "results": 2, "rss_mb": 100.7, "selected_id": "lst_011", "selected_price": 27.0, "status": 200, "ts": "2026-11-17T17:21:52.992+00:00", "uptime_s": 552, "wardrobe_items": 10}
{"agent_ms": 31926, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 31926, "error": null, "fit_card_chars": 228, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 172, "parsed": {"description": "baggy jeans", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 607, "query": "baggy jeans", "queue_wait_ms": 0, "request_id": "fd525ce2", "results": 3, "rss_mb": 100.7, "selected_id": "lst_031", "selected_price": 36.0, "status": 200, "ts": "2026-11-17T17:22:10.795+00:00", "uptime_s": 584, "wardrobe_items": 10}
{"agent_ms": 16341, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.2, "duration_ms": 16341, "error": null, "fit_card_chars": 194, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 171, "parsed": {"description": "leather bag", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 596, "query": "leather bag", "queue_wait_ms": 0, "request_id": "57fa5807", "results": 4, "rss_mb": 100.8, "selected_id": "lst_039", "selected_price": 38.0, "status": 200, "ts": "2026-11-17T17:22:42.892+00:00", "uptime_s": 600, "wardrobe_items": 10}
{"agent_ms": 77373, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.2, "duration_ms": 77373, "error": null, "fit_card_chars": 212, "model": "gemini-3.5-flash-lite", "model_calls": 3, "outcome": "ok", "output_tokens": 187, "parsed": {"description": "black jacket", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 610, "query": "black jacket", "queue_wait_ms": 0, "request_id": "251db922", "results": 10, "rss_mb": 100.8, "selected_id": "lst_022", "selected_price": 75.0, "status": 200, "ts": "2026-11-17T17:22:59.401+00:00", "uptime_s": 678, "wardrobe_items": 10}
{"agent_ms": 17159, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.2, "duration_ms": 17161, "error": null, "fit_card_chars": 167, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 124, "parsed": {"description": "white sneakers", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 567, "query": "white sneakers", "queue_wait_ms": 2, "request_id": "d92aa3b7", "results": 6, "rss_mb": 100.8, "selected_id": "lst_019", "selected_price": 48.0, "status": 200, "ts": "2026-11-17T17:24:16.938+00:00", "uptime_s": 695, "wardrobe_items": 10}
{"agent_ms": 12913, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 12914, "error": "Nothing matched \"designer ballgown\" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.", "fit_card_chars": 0, "model": "gemini-3.5-flash-lite", "model_calls": 0, "outcome": "no_results", "output_tokens": 0, "parsed": {"description": "designer ballgown", "max_price": 5.0, "size": "XXS"}, "peak_rss_mb": 100.3, "prompt_tokens": 0, "query": "designer ballgown size XXS under $5", "queue_wait_ms": 0, "request_id": "975a6dec", "results": 0, "rss_mb": 100.8, "selected_id": null, "selected_price": null, "status": 200, "ts": "2026-11-17T17:24:34.295+00:00", "uptime_s": 708, "wardrobe_items": 10}
{"boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 0, "error": "missing 'query'", "model": "gemini-3.5-flash-lite", "outcome": "rejected", "peak_rss_mb": 100.3, "query": null, "request_id": "a6621abf", "rss_mb": 100.8, "status": 400, "ts": "2026-11-17T17:24:47.450+00:00", "uptime_s": 709}
{"boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 0, "error": "missing 'query'", "model": "gemini-3.5-flash-lite", "outcome": "rejected", "peak_rss_mb": 100.3, "query": null, "request_id": "fa0ba82b", "rss_mb": 100.8, "status": 400, "ts": "2026-11-17T17:24:47.589+00:00", "uptime_s": 709}
{"boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 0, "error": "missing 'query'", "model": "gemini-3.5-flash-lite", "outcome": "rejected", "peak_rss_mb": 100.3, "query": null, "request_id": "bd2aad50", "rss_mb": 100.8, "status": 400, "ts": "2026-11-17T17:24:47.775+00:00", "uptime_s": 709}
```

## Errors the caller saw

- `{"query": "designer ballgown size XXS under $5"}` → 200: Nothing matched "designer ballgown" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.
- `{}` → 400: Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee under $30"}
- `{"query": "   "}` → 400: Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee under $30"}
- `this is not json` → 400: Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee under $30"}
