# Live run — instrumentation

- URL: https://fitfindr-8uv3.onrender.com
- When: 2026-11-17T17:03:33.068+00:00 (UTC)
- `/health` before the run: 316 ms
- Requests: 14, 1 at a time
- With a matching server log record: 0 of 14
- Server boot ids seen (more than one = it restarted): -

| # | kind | request body | HTTP | client ms | server outcome | server ms | queue ms | calls | tokens in/out | rss MB | child peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ok | `{"query": "vintage graphic tee under $30"}` | 200 | 27364 | NOT LOGGED | - | - | - | - | - | - |
| 2 | ok | `{"query": "denim jacket under $50"}` | 200 | 13634 | NOT LOGGED | - | - | - | - | - | - |
| 3 | ok | `{"query": "90s track jacket size M"}` | 502 | 556 | NOT LOGGED | - | - | - | - | - | - |
| 4 | ok | `{"query": "silk slip dress under $40"}` | 502 | 730 | NOT LOGGED | - | - | - | - | - | - |
| 5 | ok | `{"query": "platform sneakers size 8"}` | 502 | 252 | NOT LOGGED | - | - | - | - | - | - |
| 6 | ok | `{"query": "cargo pants under $40"}` | 502 | 226 | NOT LOGGED | - | - | - | - | - | - |
| 7 | ok | `{"query": "baggy jeans"}` | 502 | 241 | NOT LOGGED | - | - | - | - | - | - |
| 8 | ok | `{"query": "leather bag"}` | 502 | 255 | NOT LOGGED | - | - | - | - | - | - |
| 9 | ok | `{"query": "black jacket"}` | 502 | 306 | NOT LOGGED | - | - | - | - | - | - |
| 10 | ok | `{"query": "white sneakers"}` | 502 | 183 | NOT LOGGED | - | - | - | - | - | - |
| 11 | no_match | `{"query": "designer ballgown size XXS under $5"}` | 502 | 259 | NOT LOGGED | - | - | - | - | - | - |
| 12 | bad_input | `{}` | 502 | 234 | NOT LOGGED | - | - | - | - | - | - |
| 13 | bad_input | `{"query": "   "}` | 502 | 204 | NOT LOGGED | - | - | - | - | - | - |
| 14 | bad_input | `this is not json` | 502 | 197 | NOT LOGGED | - | - | - | - | - | - |

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

- `{"query": "90s track jacket size M"}` → 502: non-JSON response: 
- `{"query": "silk slip dress under $40"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "platform sneakers size 8"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "cargo pants under $40"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "baggy jeans"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "leather bag"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "black jacket"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "white sneakers"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "designer ballgown size XXS under $5"}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `{"query": "   "}` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
- `this is not json` → 502: non-JSON response: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-fami
