"""One-off comparison of the two Onevie exports to understand how they relate
before building a combined analysis on top of them."""
import pandas as pd

a = pd.read_csv("data/aihs-door-checkins.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
b = pd.read_csv("data/aihs-day2-main-session.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)

print(f"aihs-door-checkins.csv: {len(a)} rows")
print(f"aihs-day2-main-session.csv: {len(b)} rows")

key_cols = ["Full name", "Email", "Ticket type", "Checked in at (Africa/Lagos)"]


def row_key(df):
    return set(df[key_cols].apply(lambda r: tuple(r), axis=1))


ka, kb = row_key(a), row_key(b)
print(f"\nIdentical row-sets (name+email+ticket+time)? {ka == kb}")
print(f"Rows in A not in B: {len(ka - kb)}")
print(f"Rows in B not in A: {len(kb - ka)}")

only_a = ka - kb
only_b = kb - ka
if only_a:
    print("\n-- Sample rows only in door-checkins.csv --")
    for r in list(only_a)[:10]:
        print(r)
if only_b:
    print("\n-- Sample rows only in day2-main-session.csv --")
    for r in list(only_b)[:10]:
        print(r)

# Email-only comparison (ignoring exact row match) in case of minor field diffs
email_a = set(a["Email"].str.strip().str.lower())
email_b = set(b["Email"].str.strip().str.lower())
print(f"\nUnique emails in A: {len(email_a)}")
print(f"Unique emails in B: {len(email_b)}")
print(f"Emails in A not in B: {len(email_a - email_b)}")
print(f"Emails in B not in A: {len(email_b - email_a)}")
