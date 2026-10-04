# log_util.py
# A simple in-memory logger. Modernized 2025.

import time

LOG_LINES: list[str] = []  # module-level buffer; cleared on each flush


def log(message: str) -> None:
    """Append a timestamped line to the buffer and print it."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    LOG_LINES.append(line)
    print(line)


def flush_log(path: str) -> None:
    """Write buffered log lines to a file and clear the buffer."""
    with open(path, "a") as f:
        for line in LOG_LINES:
            f.write(line + "\n")
    LOG_LINES.clear()
