# AI in Health Summit 2026 — Executive Report Package

**How to use this**: Paste this whole document into a new Claude.ai (web) conversation, then upload the PNG chart files listed under each section (they're in `tools/checkin-analytics/output/` and `tools/checkin-analytics/output-full-event/`). Ask Claude web to turn this into an executive report and/or a slide deck — all the real numbers, findings, and recommendations are already here; nothing needs to be invented or estimated.

Suggested prompt to use on Claude web:
> "Using the attached data and charts, write an executive post-event report for AHFID leadership on the AI in Health Summit 2026, and build a slide deck covering: event overview, attendance & demographics, what worked, what needs to improve, and recommendations for next year. Use only the real numbers provided — don't estimate or invent anything not in this document."

---

## 1. Event Overview

- **AI in Health Summit 2026**, Abuja, Nigeria — two days, 19–20 October 2026.
- 1,158 total registrations across all categories (attendee, speaker, VIP, volunteer, exhibitor, innovator, sponsor, staff); 883 confirmed.
- Satellite programs: AI in Health Masterclass (Day 1), Women in AI & Health Breakfast, High-Level Ministerial Roundtable Dialogue (Day 2).

## 2. Full-Event Attendance & Demographics

*Source: door check-in export (667 records, 666 valid after excluding one data anomaly), cross-referenced with the registration database for demographics.*

**Attach these charts**: `tools/checkin-analytics/output-full-event/attendance_by_day.png`, `by_ticket_type.png`, `by_method.png`, `arrivals_2026-10-19.png`, `arrivals_2026-10-20.png`, `gender_split.png`, `country_split.png`, `top_organizations.png`

Full detail below (also in `tools/checkin-analytics/output-full-event/summary.md`):

<details>
<summary>Full attendance & demographics summary</summary>

666 distinct people were scanned in at the door across the two-day event — each badge is recorded checking in only once, so the split below is **first-arrival day**, not a daily headcount (someone who arrived Day 1 and returned Day 2 generates no second scan event).

**Headline**

| First check-in day | People |
| --- | ---: |
| Day 1 (19 Oct) | 559 |
| Day 2 (20 Oct) | 107 |
| **Total** | **666** |

The 107 figure for Day 2 counts only people whose *first-ever* scan happened that day (largely Day-2-only guests, e.g. VIPs arriving for the afternoon Roundtable) — it understates real Day 2 room attendance, since returning Day 1 attendees don't re-scan. A true daily headcount needs a check-in system that logs each day's entry separately.

1 check-in record fell outside the event dates and was excluded from the figures above (see Data Notes).

**Arrival Pattern**

- Day 1 (19 Oct): first check-in 00:19, last 17:26, peak window 08:30–08:45 (49 check-ins).
- Day 2 (20 Oct): first check-in 07:34, last 15:29, peak window 14:15–14:30 (10 check-ins).

**Ticket Type Mix**

| Ticket type | Check-ins |
| --- | ---: |
| Delegate | 430 |
| Speaker | 76 |
| VIP | 38 |
| Volunteer | 37 |
| Media | 27 |
| Organizer | 21 |
| Exhibitor | 20 |
| Innovator | 17 |

**Check-In Method**

195 of 666 check-ins (29.3%) needed manual name search at the door instead of a working QR scan.

| Day | Manual search rate |
| --- | ---: |
| Day 1 (19 Oct) | 34.0% |
| Day 2 (20 Oct) | 4.7% |

**Demographics** (of checked-in attendees matched to a registration; matched 91.0% of distinct checked-in people by email)

| Gender | Count |
| --- | ---: |
| Not Stated | 388 |
| Male | 116 |
| Female | 101 |
| Prefer Not To Say | 1 |

| Country | Count |
| --- | ---: |
| Nigeria | 452 |
| Unknown | 146 |
| Ghana | 3 |
| United Kingdom | 2 |
| Uganda | 2 |
| Saudi Arabia | 1 |

Top organizations: see `top_organizations.png`.

**Data Notes**

- **Day 1 vs Day 2 is first-arrival day, not a daily headcount.** No email appears twice in this export — each badge is scanned exactly once across the whole event. Getting a real per-day headcount next year requires a check-in flow that logs a fresh scan each day.
- `aihs-day2-main-session.csv` was found to be an exact subset of `aihs-door-checkins.csv` (412 of its 412 rows all appear in the 667-row file) and was not used — the 667-row file is the authoritative source.
- **Anomaly excluded**: "Dr Kunle Kakanfo" shows a check-in timestamp of 2026-10-23 11:07, three days after the event ended — almost certainly a stray/test scan, not real Day 1/2 attendance.
- Gender is stated for 218 of 606 checked-in people matched to a registration (36.0% of those matched) — it's an optional field, so this is a partial picture.
- Country values had inconsistent capitalization/variants ("Nigeria" / "NIGERIA" / "Nigerian") and were normalized before counting.
- 9.0% of checked-in people could not be matched to a confirmed registration by email — likely booth staff, last-minute walk-ins under a different email, or group-registration members without their own record.

</details>

## 3. Women Delegate Program — Day 1 Attendance

*Source: a separate check-in export specific to the "Women Delegate" ticket category (175 registrants).*

**Attach these charts**: `tools/checkin-analytics/output/attendance.png`, `arrivals.png`, `cumulative.png`

<details>
<summary>Full Women Delegate summary</summary>

**Headline**

- Registered: 175
- Checked in: 84
- Absent: 91
- Attendance rate: 48.0%

**Arrival Pattern**

- First check-in: 07:38 WAT
- Last check-in: 10:14 WAT
- Peak 15-minute window: 08:00–08:15 (18 check-ins)

**Email Domain Split**

- Personal email domains (gmail, yahoo, outlook, hotmail, icloud, ymail): 135
- Organisational domains: 40

_Based on email domain only, not confirmed organisation._

| Domain | Registrants | Checked In | Attendance Rate |
| --- | ---: | ---: | ---: |
| miva.edu.ng | 6 | 3 | 50.0% |
| apin.org.ng | 2 | 2 | 100.0% |
| mhrinitiative.org | 2 | 1 | 50.0% |
| evanigeria.org | 2 | 1 | 50.0% |

</details>

## 4. Lessons Learned & Recommendations for Next Year

This is the strategic core of the report — what to keep, what to fix, and what to upgrade or remove, based on real incidents from this event cycle.

<details>
<summary>Full lessons-learned & recommendations report</summary>

**What worked well (keep doing this)**

- Badge QR access, once synced, worked for the large majority of check-ins: 70.7% of all door check-ins were a clean QR scan with no staff intervention.
- One unified registration system across every ticket type (attendee, speaker, VIP, volunteer, exhibitor, innovator, sponsor, staff) made it possible to report on the whole event from one source.
- The Session Attendance tool, where it was used, gave real per-room attendance data that door check-in alone can never provide.
- A late-built feedback-invite system (personal email links to the feedback form) is now reusable infrastructure for next year.

**What to fix before next year**

1. **QR check-in reliability (highest priority)**. 29.3% of all door check-ins (195 of 666) needed manual name search because the QR scan didn't work. Root causes this cycle included printed badge QR codes differing from the emailed QR for some group-registration members, and the vendor's system occasionally generating its own QR code when our check-in token wasn't passed through correctly. *Recommendation*: run a full dry test of the registration → vendor sync → badge print → door scan pipeline on real badges before printing at scale, and treat any QR mismatch as a release blocker.

2. **Vendor ticket-type capacity must be set from real projections**. The door-scanning vendor's "Speaker" ticket type had a hard capacity that was exceeded once confirmed speakers passed that number. *Recommendation*: share projected headcounts per ticket category with the vendor at least two weeks out, with headroom, and get written confirmation before badges are finalized.

3. **No walk-in registrations directly in the vendor's system**. Evidence pointed to some walk-ins being registered directly in the vendor's own admin tool at the door, creating a duplicate identity with a different QR code. *Recommendation*: every walk-in should be entered into our own registration system first (auto-generates a real QR in seconds), never directly into the vendor's tool.

4. **Real per-day attendance isn't currently measurable**. Every badge in the vendor's export is scanned exactly once for the whole event — there's no second scan when a Day 1 attendee returns Day 2, so the Day 2 figure in this report is first-arrival day, not a real Day 2 headcount. *Recommendation*: if a true daily headcount matters next year, the check-in flow needs to log a fresh scan each day.

5. **Registration follow-up was reactive, not scheduled**. At points this cycle, roughly a quarter of all registrations sat in "pending" status, requiring a dedicated reconfirmation campaign to be built and run. *Recommendation*: build reminder nudges into the registration timeline itself (e.g., automatic at 3 weeks, 1 week, 48 hours out).

6. **Demographic data is too sparse and inconsistent to report on confidently**. Only about a third of confirmed registrants have a stated gender (optional field), and country is free text with inconsistent variants. *Recommendation*: make gender more visibly encouraged if not required, and replace free-text country with a dropdown.

7. **Session Attendance adoption was partial**. Only a handful of sessions on the full agenda had any volunteer QR scanning activity recorded. *Recommendation*: brief every room volunteer on the tool during pre-event orientation, with a one-page guide per room.

8. **Satellite sessions (Masterclass, Women in AI & Health Breakfast, Ministerial Roundtable) were built reactively**, each needing custom RSVP/check-in logic under time pressure. *Recommendation*: scope these needs during initial platform planning if they repeat next year.

9. **Website funnel: strong interest, softer conversion to registration**. The Agenda page drew far more traffic than the Register page. *Recommendation*: add a persistent "Register" call-to-action across high-traffic pages and track clicks on it directly.

**Summary table**

| Area | Severity | Fix owner |
| --- | --- | --- |
| QR check-in reliability | High | Platform + vendor pipeline test |
| Vendor ticket-type capacity | High | Vendor coordination |
| Walk-in registration process | Medium | Front-desk policy/training |
| Daily attendance tracking | Medium | Platform feature (if needed next year) |
| Registration follow-up automation | Medium | Platform feature |
| Demographic data quality | Low–Medium | Form design change |
| Session Attendance adoption | Medium | Volunteer training/process |
| Satellite session planning | Low | Project planning timeline |
| Website registration funnel | Low–Medium | Marketing/UX |

</details>

## 5. Notes for Whoever Builds the Final Report

- Every number in this package is computed from real data (either the vendor's check-in export or this platform's own registration database) — none of it is estimated.
- The "Day 2" attendance figure is **first-arrival day**, not a Day 2 headcount — see the explicit caveat in Section 2's data notes before presenting it as same-day attendance.
- Gender and country demographics are partial (gender ~36% stated, country ~91% matched) — present these as "of those who stated it," not as full-population splits.
- The Women Delegate numbers (Section 3) and the full-event numbers (Section 2) come from two different exports and aren't meant to be added together — the Women Delegate ticket category is a subset tracked separately for that program's own reporting needs.
