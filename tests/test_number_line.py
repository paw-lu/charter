"""Test the number line generator."""
from typing import Sequence
from typing import Tuple
from typing import Union

import pytest

from charter import number_line


@pytest.mark.parametrize("number, expected_power", [(1e3, 3), (200e6, 6), (100e-3, -3)])
def test__find_closest_prefix_power(
    number: Union[int, float], expected_power: int
) -> None:
    """It finds the closest power associated to an SI prefix."""
    assert expected_power == number_line._find_closest_prefix_power(number)


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
def test_make_tick_labels(
    ticks: Sequence[Union[int, float]], expected_tick_labels: Tuple[str]
) -> None:
    """It formats the ticks for display."""
    tick_labels = tuple(number_line.make_tick_labels(ticks))
    assert tick_labels == expected_tick_labels
