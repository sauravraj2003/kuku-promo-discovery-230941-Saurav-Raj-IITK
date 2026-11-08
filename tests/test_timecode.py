"""AC03: Integer centisecond arithmetic for parse_time / format_time."""
import pytest
from kuku.timecode import parse_time, format_time, union_duration


# ---------------------------------------------------------------------------
# parse_time
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_cs", [
    ("00:00.00", 0),
    ("00:01.00", 100),        # 1 second = 100 cs
    ("01:00.00", 6000),       # 1 minute = 6000 cs
    ("01:19.00", 7900),       # AC03/AC04 reference value
    ("02:11.50", 13150),      # AC04 reference value – end of E23 window
    ("00:19.99", 1999),       # just under 20 s
    ("00:20.00", 2000),       # exactly 20 s (minimum promo)
    ("01:00.00", 6000),       # exactly 60 s (maximum promo)
    ("01:00.01", 6001),       # just over 60 s
    ("59:59.99", 359999),     # large value
])
def test_parse_time_exact(text, expected_cs):
    assert parse_time(text) == expected_cs


def test_parse_time_e23_window_duration():
    """AC04: 01:19.00–02:11.50 must be exactly 52.50 seconds = 5250 cs."""
    start = parse_time("01:19.00")
    end = parse_time("02:11.50")
    assert start == 7900
    assert end == 13150
    assert end - start == 5250


@pytest.mark.parametrize("bad", [
    "1:00.00",   # single-digit minute
    "00:60.00",  # second overflow
    "00:00.0",   # one hundredths digit
    "00:00",     # missing hundredths
    "ab:cd.ef",
    "",
    "00:00.00 ",
])
def test_parse_time_rejects_invalid(bad):
    with pytest.raises(ValueError):
        parse_time(bad)


# ---------------------------------------------------------------------------
# format_time
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cs,expected", [
    (0, "00:00.00"),
    (100, "00:01.00"),
    (6000, "01:00.00"),
    (7900, "01:19.00"),
    (13150, "02:11.50"),
    (1999, "00:19.99"),
    (2000, "00:20.00"),
    (6001, "01:00.01"),
])
def test_format_time_exact(cs, expected):
    assert format_time(cs) == expected


def test_format_time_rejects_negative():
    with pytest.raises(ValueError):
        format_time(-1)


def test_format_time_rejects_non_int():
    with pytest.raises(ValueError):
        format_time(1.5)  # type: ignore


def test_roundtrip():
    """parse_time and format_time are inverses for all representable values."""
    for cs in range(0, 100000, 37):
        assert parse_time(format_time(cs)) == cs


# ---------------------------------------------------------------------------
# union_duration – AC06 simultaneous-tracks arithmetic
# ---------------------------------------------------------------------------

def test_union_duration_disjoint():
    assert union_duration([(0, 100), (200, 300)]) == 200


def test_union_duration_overlapping():
    """AC06: camera 0–480 and action 100–480 → union is 480, not 860."""
    assert union_duration([(0, 480), (100, 480)]) == 480


def test_union_duration_adjacent():
    assert union_duration([(0, 100), (100, 200)]) == 200


def test_union_duration_empty():
    assert union_duration([]) == 0


def test_union_duration_single():
    assert union_duration([(50, 150)]) == 100
