# Live run — cost

- URL: https://fitfindr-8uv3.onrender.com
- When: 2026-11-17T17:07:17.070+00:00 (UTC)
- `/health` before the run: 298 ms
- Requests: 10, 1 at a time
- With a matching server log record: 0 of 10
- Server boot ids seen (more than one = it restarted): -

| # | kind | request body | HTTP | client ms | server outcome | server ms | queue ms | calls | tokens in/out | rss MB | child peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ok | `{"query": "vintage graphic tee under $30"}` | 200 | 21498 | NOT LOGGED | - | - | - | - | - | - |
| 2 | ok | `{"query": "denim jacket under $50"}` | 200 | 13069 | NOT LOGGED | - | - | - | - | - | - |
| 3 | ok | `{"query": "90s track jacket size M"}` | 200 | 14805 | NOT LOGGED | - | - | - | - | - | - |
| 4 | ok | `{"query": "silk slip dress under $40"}` | 200 | 7849 | NOT LOGGED | - | - | - | - | - | - |
| 5 | ok | `{"query": "platform sneakers size 8"}` | 502 | 588 | NOT LOGGED | - | - | - | - | - | - |
| 6 | ok | `{"query": "cargo pants under $40"}` | 502 | 157 | NOT LOGGED | - | - | - | - | - | - |
| 7 | ok | `{"query": "baggy jeans"}` | 502 | 345 | NOT LOGGED | - | - | - | - | - | - |
| 8 | ok | `{"query": "leather bag"}` | 502 | 344 | NOT LOGGED | - | - | - | - | - | - |
| 9 | ok | `{"query": "black jacket"}` | 502 | 123 | NOT LOGGED | - | - | - | - | - | - |
| 10 | ok | `{"query": "white sneakers"}` | 502 | 138 | NOT LOGGED | - | - | - | - | - | - |

## Averages over requests with outcome `ok`

- Runs: 0
- Model calls: None
- Prompt tokens: None
- Output tokens: None
- Server duration ms: None

## Server log records (from GET /logs, written by serve.py::_log)

```
```

## Errors the caller saw

- `{"query": "platform sneakers size 8"}` → 502: non-JSON response: 
- `{"query": "cargo pants under $40"}` → 502: non-JSON response: 
- `{"query": "baggy jeans"}` → 502: non-JSON response: 
- `{"query": "leather bag"}` → 502: non-JSON response: 
- `{"query": "black jacket"}` → 502: non-JSON response: 
- `{"query": "white sneakers"}` → 502: non-JSON response: 
