"""Test the number line generator."""
from typing import List
from typing import Tuple

import pytest

from charter import axis


def test_tick_labels() -> None:
    """It generates tick labels."""
    ticks = axis.Ticks(min_data=123456 + 1, max_data=123456 + 11, max_ticks=14)
    assert ticks.tick_labels == [
        "57.00",
        "58.00",
        "59.00",
        "60.00",
        "61.00",
        "62.00",
        "63.00",
        "64.00",
        "65.00",
        "66.00",
        "67.00",
    ]


def test_unequal_tick_labels() -> None:
    """It raises a ValueError when value do not match label lengths."""
    with pytest.raises(ValueError):
        axis.Ticks(
            min_data=0,
            max_data=10,
            max_ticks=20,
            tick_values=[1, 2, 3],
            tick_labels=["1.0", "2.0", "3.0", "4.0"],
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
    assert (
        axis._round_number(
            number=number,
            limits=limits,
            rounding_terms=rounding_terms,
            allow_equal=allow_equal,
        )
        == expected_rounded_num
    )


def test_tick_values_min_max_equal() -> None:
    """It returns equal min and maximum ticks when bounds are equal."""
    actual_tick_values = axis._get_tick_values(
        min_data=10.0, max_data=10.0, max_ticks=10
    )
    assert actual_tick_values == [10.0]


@pytest.mark.parametrize(
    "min_data, max_data, max_ticks, expected_ticks",
    [
        (0, 10, 10, [pos for pos in range(0, 11, 2)]),
        (-20, -10, 5, [pos for pos in range(-20, -9, 5)]),
        (1e6 + 5, 1e6 + 10, 10, [1e6 + pos for pos in range(5, 11, 1)]),
        (1 + 1e-7, 1 + 5e-7, 10, [1 + (1e-7 * factor) for factor in range(1, 7)]),
    ],
)
def test__get_tick_values(
    min_data: float,
    max_data: float,
    max_ticks: int,
    expected_ticks: Tuple[float, float, float],
) -> None:
    """It creates ticks."""
    actual_tick_values = axis._get_tick_values(
        min_data=min_data, max_data=max_data, max_ticks=max_ticks
    )
    assert actual_tick_values == pytest.approx(expected_ticks)


@pytest.mark.parametrize(
    "number, expected_power", [(1e3, 3), (200e6, 6), (0.1, -3), (1e-3, -3)]
)
def test__find_closest_prefix_power(number: float, expected_power: int) -> None:
    """It finds the closest power associated to an SI prefix."""
    actual_power = axis._find_closest_prefix_power(number=number)
    assert actual_power == expected_power


@pytest.mark.parametrize(
    "tick_values, axis_subtractor, tick_divisor_power, expected_tick_labels",
    [
        (
            [1.00, 1.20, 1.40, 1.60, 1.80, 2.00],
            0,
            0,
            ["1.00", "1.20", "1.40", "1.60", "1.80", "2.00"],
        ),
        ([1e6 + 3.00, 1e6 + 4.00, 1e6 + 5.00], 1e6, 0, ["3.00", "4.00", "5.00"]),
        ([5_000_003], 0, 6, ["5.00M"]),
        (
            [5_561_943 + axis_tick for axis_tick in range(6)],
            5561940,
            0,
            ["3.00", "4.00", "5.00", "6.00", "7.00", "8.00"],
        ),
        (
            [1e9 + 300.00e3, 1e9 + 400.00e3, 1e9 + 500.00e3],
            1e9,
            3,
            ["300.00k", "400.00k", "500.00k"],
        ),
    ],
)
def test__make_tick_labels(
    tick_values: List[float],
    axis_subtractor: float,
    tick_divisor_power: int,
    expected_tick_labels: List[str],
) -> None:
    """It formats the ticks for display."""
    actual_tick_labels = axis._make_tick_labels(
        tick_values=tick_values,
        axis_subtractor=axis_subtractor,
        tick_divisor_power=tick_divisor_power,
    )
    assert actual_tick_labels == expected_tick_labels


@pytest.mark.parametrize(
    "tick_values, expected_axis_subtractor, expected_tick_divisor_power",
    [
        ([1.00, 2.00, 3.00], 0, 0),
        ([2.00, 4.00, 6.00, 8.00, 10.00], 0, 0),
        ([2.00e3, 4.00e3, 6.00e3, 8.00e3, 10.00e3], 0, 3),
        ([0.00e-6, 5.00e-6, 10.00e-6, 15.00e-6], 0, -6),
        ([1.00, 1.20, 1.40, 1.60, 1.80, 2.00], 0, 0),
        ([1e6 + 3.00, 1e6 + 4.00, 1e6 + 5.00], 1e6, 0),
        ([1e6 + axis_tick / 10 for axis_tick in range(30, 50, 5)], 1e6, 0),
        ([1e9 + 300.00e3, 1e9 + 400.00e3, 1e9 + 500.00e3], 1e9, 3),
        ([1 + 10.00e-6, 1 + 20.00e-6, 1 + 30.00e-6], 1, -6),
        ([axis_tick for axis_tick in range(500, 10_001, 280)], 0, 3),
        ([axis_tick / 10 for axis_tick in range(10, 21, 1)], 0, 0),
        ([100 + axis_tick * 1e-6 for axis_tick in range(1, 11)], 100, -6),
        ([5_000_003], 0, 6),
        ([5_561_943 + axis_tick for axis_tick in range(6)], 5561940, 0),
    ],
)
def test__get_axis_label_adjustors(
    tick_values: List[float],
    expected_axis_subtractor: float,
    expected_tick_divisor_power: int,
) -> None:
    """It finds the axis power and subtractor."""
    actual_axis_subtractor, actual_tick_divisor_power = axis._get_axis_label_adjustors(
        tick_values=tick_values
    )
    assert (actual_axis_subtractor, actual_tick_divisor_power) == pytest.approx(
        (expected_axis_subtractor, expected_tick_divisor_power)
    )
