# fleet_utils.py
# Helper utilities for Vossberg Mobility fleet processing.
# Modernized 2025: dead code removed, conversion factor corrected.

MILES_PER_KM: float = 0.6214  # was 1.609 (inverted — that is km per mile, not miles per km)


def km_to_miles(km: float) -> float:
    """Convert kilometres to miles. Used by the nightly UK partner report."""
    return km * MILES_PER_KM


def format_number(value: float) -> str:
    """Format a number to one decimal place."""
    return f"{value:.1f}"


def format_percent(value: float) -> str:
    """Format a number as a whole-number percentage string."""
    return f"{int(value)}%"
