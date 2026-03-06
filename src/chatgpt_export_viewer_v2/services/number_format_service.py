from __future__ import annotations

NUMBER_FORMAT_COMPACT = "compact"
NUMBER_FORMAT_FULL = "full"


def normalize_number_format_mode(mode: str | None) -> str:
    if mode == NUMBER_FORMAT_FULL:
        return NUMBER_FORMAT_FULL
    return NUMBER_FORMAT_COMPACT


def format_quantity(value: int | float, mode: str, decimals: int = 1) -> str:
    mode = normalize_number_format_mode(mode)

    if mode == NUMBER_FORMAT_FULL:
        if isinstance(value, int):
            return f"{value:,}"
        return f"{float(value):,.{max(0, int(decimals))}f}"

    number = float(value)
    sign = "-" if number < 0 else ""
    absolute = abs(number)
    precision = max(0, int(decimals))

    suffixes = [
        (1_000_000_000_000.0, "T"),
        (1_000_000_000.0, "B"),
        (1_000_000.0, "M"),
        (1_000.0, "K"),
    ]
    for threshold, suffix in suffixes:
        if absolute >= threshold:
            scaled = absolute / threshold
            text = f"{scaled:.{precision}f}".rstrip("0").rstrip(".")
            return f"{sign}{text}{suffix}"

    if isinstance(value, int):
        return f"{int(number)}"

    text = f"{absolute:.{precision}f}".rstrip("0").rstrip(".")
    return f"{sign}{text}"
