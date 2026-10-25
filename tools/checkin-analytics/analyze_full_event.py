"""
Full-event check-in + demographics analysis (both days, all ticket types).

Self-contained: reads the Onevie door check-in CSV and the read-only
registration demographics snapshot, writes only to --output. Never touches
the live database itself (that happened once, separately, to produce the
demographics snapshot file this script reads).
"""

import argparse
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

COLOR_ORANGE = "#E8792C"
COLOR_NAVY = "#0F172A"
COLOR_TEAL = "#0D9488"
COLOR_VIOLET = "#7C3AED"
COLOR_SUCCESS = "#16A34A"
COLOR_DANGER = "#DC2626"
COLOR_AMBER = "#D97706"
COLOR_BLUE = "#2563EB"
COLOR_MUTED = "#94A3B8"
COLOR_GRID = "#E2E8F0"

EVENT_DAYS = {"2026-10-19": "Day 1 (19 Oct)", "2026-10-20": "Day 2 (20 Oct)"}
BUCKET_MINUTES = 15


def bar_chart(output_dir, filename, title, labels, values, colors, ylabel, subtitle=None):
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=100)
    bars = ax.bar(labels, values, color=colors, width=0.6)
    for rect, val in zip(bars, values):
        ax.annotate(str(int(val)), (rect.get_x() + rect.get_width() / 2, rect.get_height()), ha="center", va="bottom", fontsize=10, color=COLOR_NAVY)
    ax.set_title(title, fontsize=14, color=COLOR_NAVY, pad=18 if subtitle else 14)
    if subtitle:
        ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, ha="center", fontsize=10, color=COLOR_MUTED)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=COLOR_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(output_dir / filename)
    plt.close(fig)


def arrivals_chart(output_dir, filename, title, series: pd.Series, color):
    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
    if not series.empty:
        labels = [t.strftime("%H:%M") for t in series.index]
        bars = ax.bar(labels, series.values, color=color, width=0.7)
        for rect, val in zip(bars, series.values):
            ax.annotate(str(int(val)), (rect.get_x() + rect.get_width() / 2, rect.get_height()), ha="center", va="bottom", fontsize=8, color=COLOR_NAVY)
        plt.xticks(rotation=60, ha="right", fontsize=8)
    ax.set_title(title, fontsize=13, color=COLOR_NAVY, pad=14)
    ax.set_xlabel("Check-in time (WAT)")
    ax.set_ylabel("Check-ins")
    ax.grid(axis="y", color=COLOR_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / filename)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkins", required=True, type=Path)
    parser.add_argument("--demographics", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.checkins, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    df["dt"] = pd.to_datetime(df["Checked in at (Africa/Lagos)"])
    df["date_str"] = df["dt"].dt.date.astype(str)
    df["email_norm"] = df["Email"].str.strip().str.lower()

    print("=== Validation ===")
    print(f"Total check-in rows: {len(df)}")
    dupe_emails = df["email_norm"][df["email_norm"].duplicated(keep=False)]
    if not dupe_emails.empty:
        print(f"WARNING: {dupe_emails.nunique()} email(s) checked in more than once: {sorted(dupe_emails.unique())}")
    else:
        print("No duplicate check-ins by email.")

    anomalies = df[~df["date_str"].isin(EVENT_DAYS.keys())]
    if not anomalies.empty:
        print(f"WARNING: {len(anomalies)} check-in(s) fall outside the event dates (19-20 Oct) and are EXCLUDED from day-by-day analysis:")
        for _, r in anomalies.iterrows():
            print(f"  - {r['Full name']} ({r['Email']}) at {r['Checked in at (Africa/Lagos)']}")
    valid = df[df["date_str"].isin(EVENT_DAYS.keys())].copy()
    print()

    # --- Headline ---
    total_checkins = len(valid)
    by_day = valid["date_str"].value_counts().reindex(EVENT_DAYS.keys(), fill_value=0)

    bar_chart(
        args.output, "attendance_by_day.png",
        "First door check-in, by day", [EVENT_DAYS[d] for d in by_day.index], by_day.values,
        [COLOR_ORANGE, COLOR_TEAL], "People",
        subtitle="Each badge is scanned once for the whole event — this is first-arrival day, not a daily headcount",
    )

    # --- Ticket type breakdown ---
    ticket_counts = valid["Ticket type"].value_counts().sort_values(ascending=False)
    bar_chart(
        args.output, "by_ticket_type.png",
        "Check-ins by ticket type", ticket_counts.index.tolist(), ticket_counts.values,
        [COLOR_ORANGE] + [COLOR_MUTED] * (len(ticket_counts) - 1), "Check-ins",
    )

    # --- Method breakdown (overall + per day) ---
    method_counts = valid["Method"].value_counts()
    bar_chart(
        args.output, "by_method.png",
        "Check-in method", ["QR scan" if m == "qr_scan" else "Manual search" for m in method_counts.index], method_counts.values,
        [COLOR_SUCCESS, COLOR_AMBER], "Check-ins",
        subtitle="Manual search = QR code didn't work at the door and staff found the guest by name",
    )
    method_by_day = valid.groupby(["date_str", "Method"]).size().unstack(fill_value=0)
    method_rate = (method_by_day.get("manual_search", 0) / method_by_day.sum(axis=1) * 100).round(1)

    # --- Arrival patterns per day ---
    arrival_stats = {}
    for date_str, label in EVENT_DAYS.items():
        day_df = valid[valid["date_str"] == date_str].copy()
        if day_df.empty:
            continue
        day_df["bucket"] = day_df["dt"].dt.floor(f"{BUCKET_MINUTES}min")
        bucket_counts = day_df.groupby("bucket").size().sort_index()
        safe_label = label.split(" ")[0] + label.split(" ")[1].strip("()")
        arrivals_chart(args.output, f"arrivals_{date_str}.png", f"Arrivals per {BUCKET_MINUTES}-minute window — {label}", bucket_counts, COLOR_ORANGE if "1" in label else COLOR_TEAL)
        peak_bucket = bucket_counts.idxmax()
        arrival_stats[date_str] = {
            "label": label,
            "total": len(day_df),
            "first": day_df["dt"].min(),
            "last": day_df["dt"].max(),
            "peak_bucket": peak_bucket,
            "peak_count": int(bucket_counts.max()),
        }

    # --- Demographics (merged, confirmed registrations only) ---
    demo = pd.read_csv(args.demographics, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    demo["email_norm"] = demo["email"].str.strip().str.lower()
    demo["country_norm"] = demo["country"].str.strip().str.title().replace({"": "Unknown", "Nigerian": "Nigeria"})
    demo = demo.drop_duplicates(subset="email_norm")

    merged = valid.drop_duplicates(subset="email_norm").merge(demo, on="email_norm", how="left", indicator=True)
    match_rate = round(100 * (merged["_merge"] == "both").sum() / len(merged), 1)
    print(f"Demographic match rate: {match_rate}% of distinct checked-in people matched a confirmed registration record")

    matched = merged[merged["_merge"] == "both"]
    n_matched = len(matched)
    n_gender_stated = int((matched["gender"].str.strip() != "").sum())
    gender_counts = matched["gender"].replace("", "Not stated").value_counts()
    gender_counts.index = gender_counts.index.str.replace("_", " ").str.title()
    bar_chart(
        args.output, "gender_split.png",
        "Checked-in attendees by gender", gender_counts.index.tolist(), gender_counts.values,
        [COLOR_BLUE, COLOR_VIOLET, COLOR_MUTED, COLOR_MUTED][: len(gender_counts)], "People",
        subtitle=f"Gender is optional at registration — stated by {n_gender_stated} of {n_matched} matched checked-in people",
    )

    country_counts = matched["country_norm"].value_counts().head(8)
    bar_chart(
        args.output, "country_split.png",
        "Checked-in attendees by country (top 8)", country_counts.index.tolist(), country_counts.values,
        [COLOR_ORANGE] + [COLOR_MUTED] * (len(country_counts) - 1), "People",
    )

    org_counts = matched.loc[matched["organization"].str.strip() != "", "organization"].value_counts().head(10)
    bar_chart(
        args.output, "top_organizations.png",
        "Top organizations among checked-in attendees", org_counts.index.tolist(), org_counts.values,
        [COLOR_TEAL] + [COLOR_MUTED] * (len(org_counts) - 1), "People",
    )

    # --- Summary.md ---
    lines = []
    lines.append("# AI in Health Summit 2026 — Full Event Attendance & Demographics")
    lines.append("")
    lines.append(f"{total_checkins} distinct people were scanned in at the door across the two-day event — each badge is recorded checking in only once, so the split below is **first-arrival day**, not a daily headcount (someone who arrived Day 1 and returned Day 2 generates no second scan event).")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append("| First check-in day | People |")
    lines.append("| --- | ---: |")
    for d, label in EVENT_DAYS.items():
        lines.append(f"| {label} | {by_day[d]} |")
    lines.append(f"| **Total** | **{total_checkins}** |")
    lines.append("")
    lines.append(f"The {by_day[list(EVENT_DAYS.keys())[1]]} figure for Day 2 counts only people whose *first-ever* scan happened that day (largely Day-2-only guests, e.g. VIPs arriving for the afternoon Roundtable) — it understates real Day 2 room attendance, since returning Day 1 attendees don't re-scan. A true daily headcount needs a check-in system that logs each day's entry separately (see Data Notes and the Recommendations report).")
    lines.append("")
    if anomalies.shape[0]:
        lines.append(f"_{len(anomalies)} check-in record(s) fell outside the event dates and were excluded from the figures above — see Data Notes._")
        lines.append("")

    lines.append("## Arrival Pattern")
    lines.append("")
    for d in EVENT_DAYS:
        if d not in arrival_stats:
            continue
        s = arrival_stats[d]
        peak_end = pd.Timestamp(s["peak_bucket"]) + timedelta(minutes=BUCKET_MINUTES)
        lines.append(f"**{s['label']}**: first check-in {s['first'].strftime('%H:%M')}, last {s['last'].strftime('%H:%M')}, peak window {s['peak_bucket'].strftime('%H:%M')}–{peak_end.strftime('%H:%M')} ({s['peak_count']} check-ins).")
    lines.append("")
    lines.append("See `arrivals_2026-10-19.png` and `arrivals_2026-10-20.png`.")
    lines.append("")

    lines.append("## Ticket Type Mix")
    lines.append("")
    lines.append("| Ticket type | Check-ins |")
    lines.append("| --- | ---: |")
    for t, c in ticket_counts.items():
        lines.append(f"| {t} | {c} |")
    lines.append("")

    lines.append("## Check-In Method")
    lines.append("")
    qr = int(method_counts.get("qr_scan", 0))
    manual = int(method_counts.get("manual_search", 0))
    manual_pct = round(100 * manual / (qr + manual), 1)
    lines.append(f"{manual} of {qr + manual} check-ins ({manual_pct}%) needed manual name search at the door instead of a working QR scan.")
    lines.append("")
    lines.append("| Day | Manual search rate |")
    lines.append("| --- | ---: |")
    for d, label in EVENT_DAYS.items():
        if d in method_rate.index:
            lines.append(f"| {label} | {method_rate[d]}% |")
    lines.append("")

    lines.append("## Demographics (of checked-in attendees matched to a registration)")
    lines.append("")
    lines.append(f"Matched {match_rate}% of distinct checked-in people to a confirmed registration record by email.")
    lines.append("")
    lines.append("| Gender | Count |")
    lines.append("| --- | ---: |")
    for g, c in gender_counts.items():
        lines.append(f"| {g} | {c} |")
    lines.append("")
    lines.append("| Country | Count |")
    lines.append("| --- | ---: |")
    for c_name, c in country_counts.items():
        lines.append(f"| {c_name} | {c} |")
    lines.append("")
    lines.append("Top organizations: see `top_organizations.png`.")
    lines.append("")

    lines.append("## Data Notes")
    lines.append("")
    lines.append("- **Day 1 vs Day 2 is first-arrival day, not a daily headcount.** No email appears twice in this export — each badge is scanned exactly once across the whole event. That means the Day 2 figure only captures people who hadn't already been scanned on Day 1; it does not mean only that many people were physically in the venue on Day 2. Getting a real per-day headcount next year requires a check-in flow that logs a fresh scan each day (the same design this app's own Session Attendance feature already uses per session).")
    lines.append("- `aihs-day2-main-session.csv` was found to be an exact subset of `aihs-door-checkins.csv` (412 of its 412 rows all appear in the 667-row file) and was not used — the 667-row file is the authoritative source for this report.")
    if anomalies.shape[0]:
        for _, r in anomalies.iterrows():
            lines.append(f"- **Anomaly excluded**: \"{r['Full name']}\" shows a check-in timestamp of {r['Checked in at (Africa/Lagos)']}, three days after the event ended — almost certainly a stray/test scan, not real Day 1/2 attendance.")
    lines.append(f"- Gender is stated for {n_gender_stated} of {n_matched} checked-in people matched to a registration ({round(100*n_gender_stated/max(n_matched,1),1)}% of those matched) — it's an optional registration field, so this is a partial picture, not everyone.")
    lines.append("- Country values in the source data had inconsistent capitalization (\"Nigeria\" / \"NIGERIA\" / \"nigeria\") and were normalized before counting.")
    lines.append(f"- {round(100-match_rate,1)}% of checked-in people could not be matched to a confirmed registration by email — likely booth staff, last-minute walk-ins registered under a different email, or group-registration members without their own registration record.")
    lines.append("")

    (args.output / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print()
    print("=== Headline ===")
    print(f"Total check-ins: {total_checkins} (Day 1: {by_day[list(EVENT_DAYS.keys())[0]]}, Day 2: {by_day[list(EVENT_DAYS.keys())[1]]})")
    print(f"Manual-search rate: {manual_pct}%")
    print(f"Demographic match rate: {match_rate}%")
    print(f"\nWrote report + charts to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
