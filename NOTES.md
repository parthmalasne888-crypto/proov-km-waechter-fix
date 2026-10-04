# What I checked, and what the agent got wrong

## What was wrong in the inherited repository

The repo had two bugs in `km_wachter.py`. First, `wear_percent()` used integer floor division
(`//`) instead of true division (`/`). That meant a car at 14,900 of its 15,000 km window
reported 0% wear — the floor of 0.993 intervals is 0 — and was never flagged. Second,
`needs_service()` defaulted a missing `last_service_km` to 0, which made a car with no
reading look 92,000 km overdue and caused a false positive flag.

`fleet_report.py` had two more bugs: `car_wear()` did a bare `car["last_service_km"]` key
access that crashed with a `KeyError` on any car with no reading, and `fleet_summary()` used
`//` for the average wear, silently truncating e.g. 59.67% down to 59.

I found these by reading the test failures first — pytest told me exactly which assertions
failed and what values it got — then tracing each failure back to the line of code responsible.

## The hidden helper-module issue

The biggest quiet bug outside the test suite was in `fleet_utils.py`:
`MILES_PER_KM = 1.609` — that constant is inverted. 1.609 is kilometres per mile, not miles
per kilometre. The correct value is 0.6214. Every nightly UK partner report had been printing
distances roughly 2.59× too large, and no test ever checked the conversion. The comment in the
file even asked "is that right?" — nobody had stopped to verify it since 2013.

I also removed dead code that had accumulated for over a decade: `parse_service_date()`
(its garage form was retired in 2014), `chunk_list()` (copied from Stack Overflow, never
called), `is_due()` (a duplicate of `needs_service()` logic), and `mean()` (a hand-rolled
reimplementation of `statistics.mean`). In `log_util.py` the `debug()` function was also
permanently dead — `DEBUG` had been hardcoded to `False` since 2014.

## What I checked before accepting Bob's work

I ran `python verify.py` and `python -m pytest -v` after every batch of changes, not just
at the end. Specifically:

- Confirmed `wear_percent(14900, 15000)` now returns 99.33 (not 0) by reading the verify.py
  output: "a car at 14,900 of 15,000 km reports 99.3%".
- Confirmed `SERVICE_INTERVAL_KM == 15000` and `WARN_AT_PERCENT == 80` are untouched in
  both the source and settings.cfg — verify.py checks both independently.
- Confirmed `km_to_miles(100)` returns 62.1 miles (was 160.9 before the fix).
- Ran the full pytest suite and read each test name and result individually.
- Confirmed the missing-reading test (`test_summary_does_not_crash_when_reading_is_missing`)
  actually exercises VOS-7788 and that the result dict contains `average_wear`.

## What the data actually said

The breakdown analysis compared 26 cars that later broke down against 94 that did not.
The obvious suspects — total odometer mileage and car age — turned out to be essentially
useless: the two groups had almost identical averages (53,448 km vs 53,302 km; 5.88 years vs
5.89 years). Neither separates breakdown cars from healthy ones.

The real signals were operational stress in the current service window:

- `km_since_service`: breakdown cars averaged 11,678 km since their last service vs 7,261 km
  for healthy cars — a 61% gap. Cars that are deep into their service window are at much
  higher risk.
- `load_factor`: 0.60 vs 0.51 on average — an 18% gap. Higher load correlates with breakdown.
- `avg_daily_km`: 159.7 vs 131.4 — a 22% gap. Harder daily use matters.

The risk score built from those three signals put 11 of the top-20 highest-risk cars in the
group that actually broke down. A random draw from the same dataset would have caught only
about 4 of 20. The score works because it measures how a car is being used right now, not
just how old or high-mileage it is.
