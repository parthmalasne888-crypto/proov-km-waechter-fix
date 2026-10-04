# analyze.py
# Risk-factor analysis for Vossberg Mobility fleet breakdown prediction.
# Run with:  python analyze.py
#
# Findings summary (computed from fleet_history.csv, 120 cars):
# The two strongest separators between breakdown and non-breakdown cars are
# load_factor and km_since_service. avg_daily_km also contributes. Total
# odometer mileage and age_years show only a weak difference between groups —
# do NOT assume high-mileage or old cars are the primary risk; the data does
# not support that. The risk score below weights load_factor and km_since_service
# most heavily, with avg_daily_km as a secondary signal.

import sys
import pandas as pd

# Ensure UTF-8 output on Windows consoles (avoids cp1252 encoding errors).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEATURES = ["odometer_km", "km_since_service", "avg_daily_km", "load_factor", "age_years"]

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("fleet_history.csv")
total = len(df)
n_broke = df["broke_down"].sum()
print(f"\nDataset: {total} cars  |  broke down: {int(n_broke)}  |  did not: {total - int(n_broke)}\n")

# ── 2. Group comparison — which columns actually separate the two groups? ─────
broke = df[df["broke_down"] == 1]
fine  = df[df["broke_down"] == 0]

print(f"{'Column':<22} {'Mean (broke)':<16} {'Mean (ok)':<14} {'Difference':<12} {'Signal?'}")
print("-" * 76)

separations = {}
for col in FEATURES:
    m_broke = broke[col].mean()
    m_fine  = fine[col].mean()
    diff    = m_broke - m_fine
    # Flag as a useful signal if the relative difference is >= 10 %
    rel = abs(diff) / (m_fine if m_fine != 0 else 1)
    signal = "YES" if rel >= 0.10 else "weak"
    separations[col] = (diff, rel, signal)
    print(f"  {col:<20} {m_broke:<16.2f} {m_fine:<14.2f} {diff:+.2f}{'':4} {signal}")

print()
strong = [c for c in FEATURES if separations[c][2] == "YES"]
print(f"Strong signals (>=10 % relative gap): {', '.join(strong) if strong else 'none'}")
print()

# ── 3. Risk score: normalize each strong signal, weight, combine ──────────────
# Weights reflect how strongly each column separates the groups.
WEIGHTS = {
    "load_factor":       0.40,
    "km_since_service":  0.35,
    "avg_daily_km":      0.25,
}

def risk_score(row: pd.Series, col_min: dict, col_max: dict) -> float:
    """Combine normalized strong signals into a 0–100 risk score."""
    score = 0.0
    for col, weight in WEIGHTS.items():
        col_range = col_max[col] - col_min[col]
        if col_range == 0:
            continue
        norm = (row[col] - col_min[col]) / col_range
        score += norm * weight
    return round(score * 100, 1)

col_min = {c: df[c].min() for c in WEIGHTS}
col_max = {c: df[c].max() for c in WEIGHTS}

df["risk_score"] = df.apply(lambda row: risk_score(row, col_min, col_max), axis=1)

# ── 4. Print cars ranked by risk, highest first ───────────────────────────────
ranked = df[["car_id", "risk_score", "km_since_service", "avg_daily_km", "load_factor",
             "age_years", "broke_down"]].sort_values("risk_score", ascending=False)

print(f"{'Rank':<6} {'Car ID':<12} {'Risk':>6} {'km_since':>10} {'daily_km':>10} "
      f"{'load':>7} {'age':>5} {'broke'}")
print("-" * 68)
for rank, (_, row) in enumerate(ranked.iterrows(), start=1):
    marker = " <-- BROKE" if row["broke_down"] == 1 else ""
    print(f"  {rank:<4} {row['car_id']:<12} {row['risk_score']:>6.1f} "
          f"{row['km_since_service']:>10.0f} {row['avg_daily_km']:>10.0f} "
          f"{row['load_factor']:>7.2f} {row['age_years']:>5.0f}{marker}")

# ── 5. Quick validation: how many of the top-20 highest-risk cars actually broke? ─
top20_broke = ranked.head(20)["broke_down"].sum()
print(f"\nTop-20 highest-risk cars that actually broke down: {int(top20_broke)} of 20")
print("(Random baseline would be ~{:.1f} of 20)".format(20 * n_broke / total))
