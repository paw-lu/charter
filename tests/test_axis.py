"""Test the number line generator."""
from typing import Tuple

import pytest

from charter import axis


def test_ticks_repr() -> None:
    """It returns a string representation of ``Ticks``."""
    assert str(axis.Ticks(min_data=1, max_data=3, max_ticks=5)) == (
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
    ticks = axis.Ticks(min_data=1, max_data=4, max_ticks=10)
    assert (
        ticks._round_number(
            number=number,
            limits=limits,
            rounding_terms=rounding_terms,
            allow_equal=allow_equal,
        )
        == expected_rounded_num
    )


def test_tick_positions_min_max_equal() -> None:
    """It returns equal min and maximum ticks when bounds are equal."""
    ticks = axis.Ticks(min_data=10, max_data=10, max_ticks=20)
    assert ticks.tick_positions == [10.0]


@pytest.mark.parametrize(
    "min_data, max_data, max_ticks, expected_ticks",
    [
        (0, 10, 10, [pos for pos in range(0, 11, 2)]),
        (-20, -10, 5, [pos for pos in range(-20, -9, 5)]),
        (1e6 + 5, 1e6 + 10, 10, [1e6 + pos for pos in range(5, 11, 1)]),
        (1 + 1e-7, 1 + 5e-7, 10, [1 + (1e-7 * factor) for factor in range(1, 7)]),
    ],
)
def test_tick_positions(
    min_data: float,
    max_data: float,
    max_ticks: int,
    expected_ticks: Tuple[float, float, float],
) -> None:
    """It creates ticks."""
    ticks = axis.Ticks(min_data=min_data, max_data=max_data, max_ticks=max_ticks)
    assert ticks.tick_positions == pytest.approx(expected_ticks)


@pytest.mark.parametrize("number, expected_power", [(1e3, 3), (200e6, 6), (100e-3, -3)])
def test__find_closest_prefix_power(number: float, expected_power: int) -> None:
    """It finds the closest power associated to an SI prefix."""
    ticks = axis.Ticks(min_data=1, max_data=4, max_ticks=10)
    assert expected_power == ticks._find_closest_prefix_power(number)


@pytest.mark.parametrize(
    "min_data, max_data, max_ticks, expected_tick_labels",
    [
        (1, 3, 3, ("1.00", "2.00", "3.00")),
        (3.4, 10, 5, ("2.00", "4.00", "6.00", "8.00", "10.00")),
        (3.4e3, 10e3, 5, ("2.00", "4.00", "6.00", "8.00", "10.00k"),),
        (10e-8, 10e-6, 3, ("0.00", "5.00", "10.00", "15.00μ")),
        (1_000_003, 1_000_005, 3, ("3.00", "4.00", "5.00 + 1M")),
        (1_000_300_000, 1_000_500_000, 3, ("300.00k", "400.00k", "500.00k + 1G"),),
        (1.00001, 1.00003, 3, ("10.00μ", "20.00μ", "30.00μ + 1")),
    ],
)
def test_tick_labels(
    min_data: float, max_data: float, max_ticks: int, expected_tick_labels: Tuple[str]
) -> None:
    """It formats the ticks for display."""
    axis_ticks = axis.Ticks(min_data=min_data, max_data=max_data, max_ticks=max_ticks)
    tick_labels = tuple(axis_ticks.tick_labels)
    assert tick_labels == expected_tick_labels
