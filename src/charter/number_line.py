"""A unicode number line."""
import math
from typing import Generator
from typing import Sequence
from typing import Union


def _find_closest_prefix_power(number: Union[int, float]) -> int:
    """Return the closest power associated with an SI prefix.

    Args:
        number (Union[int, float]): A number to find the prefix power
            for.

    Returns:
        int: The closest SI prefix power.
    """
    return max(min(int(math.log10(number) // 3 * 3), 24), -24)


def make_tick_labels(ticks: Sequence[Union[int, float]]) -> Generator[str, None, None]:
    """Given a collection of ticks, return a formatted version.

    Args:
        ticks (Sequence[Union[int, float]]): Ticks in ascending order
            for which the labels will be generated for.

    Raises:
        TypeError: If ticks are not numerical.

    Returns:
        Generator[str, None, None]: The generated tick labels.
    """
    if any(not isinstance(tick, (int, float)) for tick in ticks):
        raise TypeError("Only numbers may be formatted.")
    metric_prefix = {
        24: "Y",
        21: "Z",
        18: "E",
        15: "P",
        12: "T",
        9: "G",
        6: "M",
        3: "k",
        -3: "m",
        -6: "μ",
        -9: "n",
        -12: "p",
        -15: "f",
        -18: "a",
        -21: "z",
        -24: "y",
    }
    step_size = ticks[1] - ticks[0]
    axis_divisor_power = _find_closest_prefix_power(ticks[-1])
    axis_prefix = metric_prefix.get(axis_divisor_power, "")
    step_place = math.log10(step_size)
    number_of_ticks = len(ticks)
    if 2 < (axis_divisor_power - math.floor(step_place)):
        tick_divisor_power = _find_closest_prefix_power(step_size)
        tick_divisor_prefix = metric_prefix.get(tick_divisor_power, "")
        return (
            f"{(tick - 10 ** axis_divisor_power) / 10 ** tick_divisor_power:0.2f}"
            f"{tick_divisor_prefix}" + (i == number_of_ticks - 1) * f" + 1{axis_prefix}"
            for i, tick in enumerate(ticks)
        )
    else:
        return (
            f"{tick / 10 ** axis_divisor_power :0.2f}"
            + (i == number_of_ticks - 1) * axis_prefix
            for i, tick in enumerate(ticks)
        )
