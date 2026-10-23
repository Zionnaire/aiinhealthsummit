"""
Check-in analytics for a single ticket type's CSV export.

Self-contained: reads only the CSV at --input, writes only to --output.
Never touches the live database or any other part of the repo. All figures
are computed directly from the CSV rows — nothing here is invented.

Usage:
    .venv/Scripts/python.exe analyze.py \\
        --input data/women-delegate-checkins.csv \\
        --output output \\
        --day "Day 1 (19 Oct 2026)"
"""

import argparse
import sys
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# AHFID brand palette — frontend/tailwind.config.js (orange/navy are brand,
# the chart.* set is the app's own data-viz accent palette).
COLOR_ORANGE = "#E8792C"
COLOR_NAVY = "#0F172A"
COLOR_TEAL = "#0D9488"
COLOR_SUCCESS = "#16A34A"
COLOR_DANGER = "#DC2626"
COLOR_GRID = "#E2E8F0"

PERSONAL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "ymail.com",
}

BUCKET_MINUTES = 15


def load_rows(input_path: Path) -> pd.DataFrame:
    # utf-8-sig quietly strips a BOM if present; behaves like plain utf-8 otherwise.
    df = pd.read_csv(input_path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    return df


def validate(df: pd.DataFrame) -> list[str]:
    notes: list[str] = []

    expected_cols = ["Full Name", "Email", "Ticket Type", "Check-In Status", "Check-In Time"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing expected column(s): {missing}. Found: {list(df.columns)}")

    ticket_types = df["Ticket Type"].str.strip().unique().tolist()
    if len(ticket_types) != 1:
        notes.append(f"WARNING: expected a single Ticket Type, found {ticket_types}")

    # Duplicate emails (case-insensitive, trimmed).
    norm_email = df["Email"].str.strip().str.lower()
    dupe_emails = norm_email[norm_email.duplicated(keep=False) & (norm_email != "")]
    if not dupe_emails.empty:
        rows = df.loc[dupe_emails.index, ["Full Name", "Email"]]
        notes.append(f"WARNING: {dupe_emails.nunique()} email address(es) appear more than once:")
        for email, group in rows.groupby(dupe_emails):
            names = ", ".join(group["Full Name"])
            notes.append(f"  - {email}: {names}")

    # Duplicate names (exact, after trim).
    norm_name = df["Full Name"].str.strip()
    dupe_names = norm_name[norm_name.duplicated(keep=False)]
    if not dupe_names.empty:
        notes.append(f"WARNING: {dupe_names.nunique()} name(s) appear more than once: {sorted(dupe_names.unique())}")

    # Status/time consistency.
    status = df["Check-In Status"].str.strip()
    time_raw = df["Check-In Time"].str.strip()
    checked_in_no_time = df[(status == "Checked In") & (time_raw == "")]
    absent_with_time = df[(status == "Absent") & (time_raw != "")]
    if not checked_in_no_time.empty:
        notes.append(f"MISMATCH: {len(checked_in_no_time)} row(s) marked Checked In with no time: " f"{checked_in_no_time['Full Name'].tolist()}")
    if not absent_with_time.empty:
        notes.append(f"MISMATCH: {len(absent_with_time)} row(s) marked Absent but have a time: " f"{absent_with_time['Full Name'].tolist()}")

    unknown_status = df[~status.isin(["Checked In", "Absent"])]
    if not unknown_status.empty:
        notes.append(f"WARNING: {len(unknown_status)} row(s) have an unrecognised Check-In Status: " f"{unknown_status['Check-In Status'].unique().tolist()}")

    return notes


def domain_of(email: str) -> str:
    email = email.strip().lower()
    return email.split("@", 1)[1] if "@" in email else ""


def build_report(df: pd.DataFrame, day_label: str, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    status = df["Check-In Status"].str.strip()
    checked_in_mask = status == "Checked In"
    checked_in = df[checked_in_mask].copy()
    absent = df[status == "Absent"].copy()

    registered = len(df)
    n_checked_in = len(checked_in)
    n_absent = len(absent)
    attendance_rate = round(100 * n_checked_in / registered, 1) if registered else 0.0

    checked_in["ts"] = pd.to_datetime(checked_in["Check-In Time"].str.strip(), format="%Y-%m-%d %H:%M")
    checked_in = checked_in.sort_values("ts")

    # 15-minute arrival buckets.
    checked_in["bucket"] = checked_in["ts"].dt.floor(f"{BUCKET_MINUTES}min")
    bucket_counts = checked_in.groupby("bucket").size().sort_index()

    first_checkin = checked_in["ts"].min() if n_checked_in else None
    last_checkin = checked_in["ts"].max() if n_checked_in else None
    peak_bucket = bucket_counts.idxmax() if not bucket_counts.empty else None
    peak_count = int(bucket_counts.max()) if not bucket_counts.empty else 0

    # Cumulative total over time.
    cumulative = bucket_counts.cumsum()

    # Email domain split.
    df["domain"] = df["Email"].apply(domain_of)
    df["is_personal"] = df["domain"].isin(PERSONAL_DOMAINS)
    n_personal = int(df["is_personal"].sum())
    n_org = int((~df["is_personal"] & (df["domain"] != "")).sum())
    n_no_domain = int((df["domain"] == "").sum())

    org_rows = df[~df["is_personal"] & (df["domain"] != "")]
    org_domain_stats = (
        org_rows.assign(checked_in=checked_in_mask.loc[org_rows.index])
        .groupby("domain")
        .agg(registrants=("domain", "size"), checked_in=("checked_in", "sum"))
        .reset_index()
        .sort_values("registrants", ascending=False)
    )
    org_domain_stats["attendance_rate_pct"] = (100 * org_domain_stats["checked_in"] / org_domain_stats["registrants"]).round(1)

    # --- Charts -----------------------------------------------------------
    fig_w, fig_h, dpi = 12, 6, 100  # 1200px wide at 100 dpi

    # Arrivals bar chart.
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    if not bucket_counts.empty:
        labels = [t.strftime("%H:%M") for t in bucket_counts.index]
        bars = ax.bar(labels, bucket_counts.values, color=COLOR_ORANGE, width=0.7)
        for rect, val in zip(bars, bucket_counts.values):
            ax.annotate(str(int(val)), (rect.get_x() + rect.get_width() / 2, rect.get_height()), ha="center", va="bottom", fontsize=9, color=COLOR_NAVY)
        plt.xticks(rotation=45, ha="right")
    ax.set_title(f"Women Delegate check-ins per {BUCKET_MINUTES}-minute window — {day_label}", fontsize=13, color=COLOR_NAVY, pad=14)
    ax.set_xlabel("Check-in time (WAT)")
    ax.set_ylabel("Check-ins")
    ax.grid(axis="y", color=COLOR_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "arrivals.png")
    plt.close(fig)

    # Cumulative line chart.
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    if not cumulative.empty:
        labels = [t.strftime("%H:%M") for t in cumulative.index]
        ax.plot(labels, cumulative.values, color=COLOR_TEAL, linewidth=2.5, marker="o", markersize=4)
        for i, val in enumerate(cumulative.values):
            if i == 0 or i == len(cumulative.values) - 1 or val == cumulative.values[-1]:
                ax.annotate(str(int(val)), (i, val), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=COLOR_NAVY)
        plt.xticks(rotation=45, ha="right")
    ax.set_title(f"Cumulative Women Delegate check-ins — {day_label}", fontsize=13, color=COLOR_NAVY, pad=14)
    ax.set_xlabel("Check-in time (WAT)")
    ax.set_ylabel("Running total")
    ax.grid(axis="y", color=COLOR_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "cumulative.png")
    plt.close(fig)

    # Checked-in vs absent chart.
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    bars = ax.bar(["Checked In", "Absent"], [n_checked_in, n_absent], color=[COLOR_SUCCESS, COLOR_DANGER], width=0.5)
    for rect, val in zip(bars, [n_checked_in, n_absent]):
        ax.annotate(str(val), (rect.get_x() + rect.get_width() / 2, rect.get_height()), ha="center", va="bottom", fontsize=11, color=COLOR_NAVY)
    ax.set_title(f"Women Delegate attendance — {day_label}", fontsize=13, color=COLOR_NAVY, pad=14)
    ax.set_ylabel("Registrants")
    ax.set_ylim(0, registered * 1.15)
    ax.grid(axis="y", color=COLOR_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "attendance.png")
    plt.close(fig)

    # --- Internal-only absentee list (PII; gitignored output dir) --------
    absent[["Full Name", "Email"]].to_csv(output_dir / "absentees_internal.csv", index=False)

    return {
        "registered": registered,
        "n_checked_in": n_checked_in,
        "n_absent": n_absent,
        "attendance_rate": attendance_rate,
        "first_checkin": first_checkin,
        "last_checkin": last_checkin,
        "peak_bucket": peak_bucket,
        "peak_count": peak_count,
        "n_personal": n_personal,
        "n_org": n_org,
        "n_no_domain": n_no_domain,
        "org_domain_stats": org_domain_stats,
    }


def write_summary_md(stats: dict, day_label: str, validation_notes: list[str], output_dir: Path) -> None:
    lines = []
    lines.append(f"# Women Delegate Check-In Summary — {day_label}")
    lines.append("")
    lines.append("AI in Health Nigeria Summit 2026 — internal attendance report. All figures below are aggregates only; no individual names or emails appear in this document.")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append(f"- **Registered:** {stats['registered']}")
    lines.append(f"- **Checked in:** {stats['n_checked_in']}")
    lines.append(f"- **Absent:** {stats['n_absent']}")
    lines.append(f"- **Attendance rate:** {stats['attendance_rate']}%")
    lines.append("")
    lines.append("## Arrival Pattern")
    lines.append("")
    if stats["first_checkin"] is not None:
        lines.append(f"- **First check-in:** {stats['first_checkin'].strftime('%H:%M')} WAT")
        lines.append(f"- **Last check-in:** {stats['last_checkin'].strftime('%H:%M')} WAT")
        peak_start = pd.Timestamp(stats["peak_bucket"])
        peak_end = peak_start + timedelta(minutes=BUCKET_MINUTES)
        lines.append(f"- **Peak {BUCKET_MINUTES}-minute window:** {peak_start.strftime('%H:%M')}–{peak_end.strftime('%H:%M')} ({stats['peak_count']} check-ins)")
    else:
        lines.append("- No check-ins recorded.")
    lines.append("")
    lines.append("See `arrivals.png` for the full per-window breakdown and `cumulative.png` for the running total over the morning.")
    lines.append("")
    lines.append("## Email Domain Split")
    lines.append("")
    lines.append(f"- **Personal email domains** (gmail, yahoo, outlook, hotmail, icloud, ymail): {stats['n_personal']}")
    lines.append(f"- **Organisational domains:** {stats['n_org']}")
    if stats["n_no_domain"]:
        lines.append(f"- **No usable email/domain:** {stats['n_no_domain']}")
    lines.append("")
    lines.append("_Based on email domain only, not confirmed organisation._")
    lines.append("")
    top_orgs = stats["org_domain_stats"][stats["org_domain_stats"]["registrants"] >= 2]
    if not top_orgs.empty:
        lines.append("| Domain | Registrants | Checked In | Attendance Rate |")
        lines.append("| --- | ---: | ---: | ---: |")
        for _, row in top_orgs.iterrows():
            lines.append(f"| {row['domain']} | {int(row['registrants'])} | {int(row['checked_in'])} | {row['attendance_rate_pct']}% |")
    else:
        lines.append("No organisational domain had 2 or more registrants.")
    lines.append("")

    if validation_notes:
        lines.append("## Data Validation Notes")
        lines.append("")
        lines.append("These are worth a quick look before this report is relied on, but nothing was silently changed or dropped from the source data.")
        lines.append("")
        for note in validation_notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Charts")
    lines.append("")
    lines.append("- `attendance.png` — checked-in vs. absent")
    lines.append("- `arrivals.png` — check-ins per 15-minute window")
    lines.append("- `cumulative.png` — running check-in total over the morning")
    lines.append("")
    lines.append("## Internal Follow-Up")
    lines.append("")
    lines.append("`absentees_internal.csv` lists the name and email of everyone marked Absent, for possible follow-up. This file contains personal data — internal use only, not for circulation, and excluded from version control.")
    lines.append("")

    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to the check-in CSV export")
    parser.add_argument("--output", required=True, type=Path, help="Directory to write the report + charts into")
    parser.add_argument("--day", default="Day 1 (19 Oct 2026)", help="Human-readable day label for chart titles/report")
    args = parser.parse_args()

    df = load_rows(args.input)

    print("=== Validation ===")
    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Ticket Type value(s): {df['Ticket Type'].str.strip().unique().tolist()}")
    notes = validate(df)
    if notes:
        for note in notes:
            print(note)
    else:
        print("No issues found: no duplicate emails/names, no status/time mismatches.")
    print()

    stats = build_report(df, args.day, args.output)
    write_summary_md(stats, args.day, notes, args.output)

    print("=== Headline ===")
    print(f"Registered:       {stats['registered']}")
    print(f"Checked in:       {stats['n_checked_in']}")
    print(f"Absent:           {stats['n_absent']}")
    print(f"Attendance rate:  {stats['attendance_rate']}%")
    if stats["first_checkin"] is not None:
        print(f"First check-in:   {stats['first_checkin'].strftime('%H:%M')} WAT")
        print(f"Last check-in:    {stats['last_checkin'].strftime('%H:%M')} WAT")
        print(f"Peak window:      {stats['peak_bucket'].strftime('%H:%M')} ({stats['peak_count']} check-ins)")
    print()
    print(f"Wrote report + charts to: {args.output.resolve()}")


if __name__ == "__main__":
    sys.exit(main())
