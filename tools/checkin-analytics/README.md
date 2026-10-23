# Check-in Analytics

A small, self-contained tool for turning a single ticket type's check-in CSV
export into an internal attendance report (summary + charts), plus a
private, non-committed follow-up list of absentees.

It does **not** touch the live database, the `Backend/` or `Frontend/`
folders, or any other part of this repo. It only reads a CSV you give it and
writes to its own `output/` folder.

## Setup (one-time)

```bash
cd tools/checkin-analytics
python3 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# .venv/bin/python -m pip install -r requirements.txt         # macOS/Linux
```

## Running it

```bash
.venv/Scripts/python.exe analyze.py \
  --input data/women-delegate-checkins.csv \
  --output output \
  --day "Day 1 (19 Oct 2026)"
```

- `--input` — path to a check-in CSV export. Expected columns:
  `Full Name, Email, Ticket Type, Check-In Status, Check-In Time`
  (`Check-In Time` as `YYYY-MM-DD HH:MM`, WAT, blank for absentees).
  The file is read as `utf-8-sig`, so a UTF-8 file with or without a BOM
  both work.
- `--output` — folder to write the report into. Created if it doesn't exist.
- `--day` — a human-readable label used in chart titles and the summary
  (e.g. `"Day 2 (20 Oct 2026)"`).

## Re-running for a different ticket type or day

The script doesn't assume "Women Delegate" or "Day 1" anywhere in its logic
— it validates whatever single `Ticket Type` value is actually in the file
and reports that. To analyze a different export, drop the new CSV into
`data/` (or anywhere) and point `--input`/`--output`/`--day` at it, e.g.:

```bash
.venv/Scripts/python.exe analyze.py \
  --input data/day2-general-checkins.csv \
  --output output-day2-general \
  --day "Day 2 (20 Oct 2026)"
```

Use a distinct `--output` folder per run so reports don't overwrite each
other — all `output*/` folders are gitignored.

If a future export mixes more than one `Ticket Type` in one file, the
validation step will print a warning rather than silently averaging them
together; split the file by ticket type first if that happens.

## What it checks before computing anything (Step 1)

- Row count and column names match what's expected.
- `Ticket Type` has exactly one value.
- Duplicate emails (case-insensitive, trimmed) and duplicate names —
  reported, never silently removed.
- Every "Checked In" row has a time, every "Absent" row doesn't — mismatches
  are reported.

All of this prints to the terminal before the report is built, so you can
sanity-check the source data first.

## Outputs (`output/`)

| File | Contents | Safe to share? |
| --- | --- | --- |
| `summary.md` | Headline numbers, arrival pattern, email-domain split, validation notes | Yes — aggregates only, no names/emails |
| `attendance.png` | Checked-in vs. absent | Yes |
| `arrivals.png` | Check-ins per 15-minute window | Yes |
| `cumulative.png` | Running check-in total over time | Yes |
| `absentees_internal.csv` | Name + email of everyone marked Absent | **No — internal only.** Contains personal data; this whole `output/` folder is gitignored. |

## Design notes

- Chart colors are pulled from the live AHFID brand palette in
  `frontend/tailwind.config.js` (orange `#E8792C`, navy `#0F172A`, teal
  `#0D9488`, success/danger green/red) so these charts read as part of the
  same visual system as everything else, without this tool importing
  anything from `frontend/`.
- No number in `summary.md` is hand-entered — every figure is computed
  directly from the CSV each time the script runs.
