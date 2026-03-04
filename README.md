# GPT Mega Export (.zip)

Desktop explorer for large ChatGPT exports with threaded parsing, lazy thread list loading, markdown thread inspection, stats, health diagnostics, and persistent SQLite cache.

## Run (Windows PowerShell)

```powershell
cd "C:\Users\Apex University\Downloads\chatgpt export viewer (sample app)\v2 (base)"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py -3 main.py
```

## Cache Behavior

- First load of a source builds a per-source SQLite cache.
- Subsequent launches use cache hit loading and skip raw JSON rescans.
- Cache identity is based on source label + export file metadata fingerprints.
- If export files change, cache is invalidated and rebuilt automatically.
- Settings page includes cache actions: rebuild current, clear current, clear all.

## Highlights

- Hardcoded default source path to your latest unzipped export.
- Background parsing and detail loading via worker threads.
- Incremental thread list updates and transparent status telemetry.
- Markdown-rendered thread detail view.
- Shared thread support and thread-level metrics.
- Dark, modern gray theme by default.
