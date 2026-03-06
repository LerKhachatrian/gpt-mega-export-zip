## 2026-03-05T18:56:48-05:00
- Added end-to-end coding vs non-coding volume metrics to global stats: messages, words, tokens (o200k), and per-class averages.
- Added pending/unclassified volume tracking (messages/words/tokens) so coding+non-coding splits can be interpreted against total global volume.
- Overhauled Overview with a new "Coding Volume Split" section showing coding/non-coding totals and averages, plus pending token/thread volume.
- Updated Stats page summary narrative to include coding/non-coding/pending volume breakdown in the same compact format mode as the rest of the app.

## 2026-03-05T18:51:26-05:00
- Fixed app-wide black separator artifacts by adding explicit splitter handle styling for both horizontal and vertical splitters.
- Added global themed scrollbar styling (dark/light) to prevent OS-default black tracks/handles from appearing in any panel.
- Applied the fix at the shared QSS layer so Threads and any other splitter/scroll surfaces stay visually consistent.

## 2026-03-05T17:34:34-05:00
- Reduced end-of-build freeze risk by throttling expensive per-batch UI recompute during heavy cache/enrichment streams.
- Added explicit finalization progress updates ("Finalizing analysis | pending …") so 100% tail work no longer appears hung.
- Tightened enrichment backlog pressure and bounded enrichment wait intervals to reduce long tail stalls at cache-build completion.
- Added O(1) cache summary count path to avoid repeated full snapshot copies during load telemetry updates.

## 2026-03-05T17:27:33-05:00
- Fixed the major UI striping artifact by removing forced background paints on passive widgets and making labels/scroll hosts transparent.
- Refined the dark theme visual hierarchy (window surface, sidebar, inputs, buttons, panels, cards) for a cleaner, modern look with better contrast balance.
- Updated the light theme baseline to match the same cleaner interaction model and surface consistency.
- Kept all runtime behavior unchanged; this pass is styling-focused for readability and polish.

## 2026-03-05T03:38:52-05:00
- Overhauled the Stats page into a modern analytics view with a hero header, status badge, summary KPI cards, and a dedicated top-threads table section.
- Improved data readability by formatting thread `updated_at` values into human-friendly date/time output instead of raw timestamps.
- Added dedicated dark/light theme styling for all Stats-specific surfaces (header, summary cards, table shell, and scoped table header/selection colors).
- Preserved existing stats behavior and number-format mode integration while making the page significantly cleaner and easier to scan.

## 2026-03-05T03:36:22-05:00
- Overhauled the Settings page into a modern sectioned layout with a polished header, grouped cards, and clearer control hierarchy.
- Added dedicated Settings visuals in both dark and light themes (section cards, row styling, tuned sliders, and action-button color tiers).
- Kept all existing Settings behavior intact: live setting emission, coding-threshold sync, number-format toggle, and cache action wiring.
- Improved Settings readability for heavy workloads with clearer helper text and spacing optimized for large-dataset workflows.

## 2026-03-05T03:32:24-05:00
- Fully overhauled Overview page layout into a modern, sectioned dashboard with a hero header, metric cards, and progress snapshot bars.
- Added cleaner information hierarchy: Core Volume, Coding Analysis, and Progress Snapshot sections for faster scanning.
- Introduced new themed visual styles (dark/light) for overview-specific panels, cards, badges, typography, and progress bars.
- Preserved live data behavior and number-format mode integration while improving readability and visual polish.

## 2026-03-05T03:29:50-05:00
- Added global compact/full number formatting mode with compact default (`24.1M`, `27.2K`).
- Added Settings control to toggle number display format and persisted the preference in session state.
- Wired number formatting through Overview, Stats, Thread list counts, status lines, and telemetry counters.
- Kept a full-number fallback mode matching prior comma-separated behavior.

## 2026-03-05T03:25:40-05:00
- Added tech-stack-agnostic coding-thread analysis (code ratio + confidence + signals) with modular classifiers/detectors.
- Implemented bounded, dedicated background enrichment workers (token + coding) with backlog throttling to avoid first-load bottlenecks/UI freeze.
- Extended cache schema/read/write paths to persist per-thread coding metrics and classification metadata.
- Added UX surfaces for coding analysis: thread type filter, confidence filter, new sort modes, list badges, Overview/Stats coding KPIs, and metadata details.
- Added tweakable coding threshold in Settings (persisted in session state) and live re-filter/re-stats behavior without full re-parse.

## 2026-03-05T03:07:13-05:00
- Added `o200k_base` token metrics across thread summaries and global stats.
- Updated cache schema/build pipeline to persist token counts (`tokens_o200k`) and surface them in cached reads.
- Implemented dedicated background token counting worker thread during cache build to avoid blocking parse/index flow.
- Exposed token stats in Overview, Stats, thread list metadata, and added token-based sorting in Threads filters.
- Bumped cache schema/parser versions so existing caches rebuild safely with token fields.
