import re


def parse_time(value: str) -> int:
    match = re.fullmatch(r"(\d{2,}):([0-5]\d)\.(\d{2})", value)
    if not match:
        raise ValueError(f"Invalid MM:SS.cc timestamp: {value!r}")
    minutes, seconds, fraction = map(int, match.groups())
    return minutes * 6000 + seconds * 100 + fraction


def format_time(value: int) -> str:
    if type(value) is not int or value < 0:
        raise ValueError("Time must be a nonnegative integer number of centiseconds")
    return f"{value // 6000:02d}:{value // 100 % 60:02d}.{value % 100:02d}"


def union_duration(intervals: list[tuple[int, int]]) -> int:
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(end, merged[-1][1])
    return sum(end - start for start, end in merged)
