"""Test the number line generator."""
from typing import Sequence
from typing import Tuple

import pytest

from charter import number_line


def test_ticks_repr() -> None:
    """It returns a string representation of ``Ticks``."""
    assert str(number_line.Ticks(data=(1, 2, 3), max_ticks=5)) == (
        "Ticks(tick_positions=(1.0, 1.5, 2.0, 2.5, 3.0),"
        " tick_labels=('1.00', '1.50', '2.00', '2.50', '3.00'))"
    )


@pytest.mark.parametrize(
    "number, limits, rounding_terms, allow_equal, expected_rounded_num",
    [
        (3, (1.5, 3, 7), (1, 2, 5), False, 5),
        (2, (1, 2, 5), (1, 2, 5), True, 2),
        (1.003, (1, 2, 5), (1, 2, 5), True, 2),
    ],
)
def test__round_number(
    number: float,
    limits: Tuple[float],
    rounding_terms: Tuple[float],
    allow_equal: bool,
    expected_rounded_num: float,
) -> None:
    """It rounds the number."""
    ticks = number_line.Ticks((1, 2, 3, 4), max_ticks=10)
    assert (
        ticks._round_number(
            number=number,
            limits=limits,
            rounding_terms=rounding_terms,
            allow_equal=allow_equal,
        )
        == expected_rounded_num
    )


def test__make_tick_positions_min_max_equal() -> None:
    """It returns equal min and maximum ticks when bounds are equal."""
    ticks = number_line.Ticks((1, 2, 3, 4), max_ticks=10)
    assert ticks._make_tick_positions(data=(10,), max_ticks=20) == [10.0]


@pytest.mark.parametrize(
    "data, max_ticks, expected_ticks",
    [
        ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), 10, [pos for pos in range(0, 11, 2)]),
        ((-20, -15, -10), 5, [pos for pos in range(-20, -9, 5)]),
        ((1e6 + 5, 1e6 + 10), 10, [1e6 + pos for pos in range(5, 11, 1)]),
        ((1 + 1e-7, 1 + 5e-7), 10, [1 + (1e-7 * factor) for factor in range(1, 7)]),
    ],
)
def test__make_tick_positions(
    data: Sequence[float], max_ticks: int, expected_ticks: Tuple[float, float, float],
) -> None:
    """It creates ticks."""
    ticks = number_line.Ticks((1, 2, 3, 4), max_ticks=10)
    assert ticks._make_tick_positions(data=data, max_ticks=max_ticks) == pytest.approx(
        expected_ticks
    )


def test__make_tick_labels_raises() -> None:
    """It raises a TypeError if not supplied with numerical values."""
    ticks = number_line.Ticks((1, 2, 3, 4), max_ticks=10)
    with pytest.raises(TypeError):
        ticks._make_tick_labels(("a", "b"))  # type: ignore


@pytest.mark.parametrize("number, expected_power", [(1e3, 3), (200e6, 6), (100e-3, -3)])
def test__find_closest_prefix_power(number: float, expected_power: int) -> None:
    """It finds the closest power associated to an SI prefix."""
    ticks = number_line.Ticks((1, 2, 3, 4), max_ticks=10)
    assert expected_power == ticks._find_closest_prefix_power(number)


@pytest.mark.parametrize(
    "ticks, expected_tick_labels",
    [
        ((1, 2, 3), ("1.00", "2.00", "3.00")),
        ((3.4, 4.5, 6.6, 7.7, 10), ("3.40", "4.50", "6.60", "7.70", "10.00")),
        (
            (3.4e3, 4.5e3, 6.6e3, 7.7e3, 10e3),
            ("3.40", "4.50", "6.60", "7.70", "10.00k"),
        ),
        ((10e-8, 20e-7, 10e-6), ("0.10", "2.00", "10.00μ")),
        ((1_000_003, 1_000_004, 1_000_005), ("3.00", "4.00", "5.00 + 1M")),
        (
            (1_000_300_000, 1_000_400_000, 1_000_500_000),
            ("300.00k", "400.00k", "500.00k + 1G"),
        ),
        ((1.00001, 1.00002, 1.00003), ("10.00μ", "20.00μ", "30.00μ + 1")),
    ],
)
def test__make_tick_labels(
    ticks: Sequence[float], expected_tick_labels: Tuple[str]
) -> None:
    """It formats the ticks for display."""
    axis_ticks = number_line.Ticks((1, 2, 3, 4), max_ticks=10)
    tick_labels = tuple(axis_ticks._make_tick_labels(ticks))
    assert tick_labels == expected_tick_labels
