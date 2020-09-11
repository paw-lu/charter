"""A unicode number line."""
import bisect
import dataclasses
import math
from typing import List
from typing import Tuple


@dataclasses.dataclass()
class Ticks:
    """Chart ticks.

    Args:
        min_data (float): The minimum value of the data for the axis
                dimension.
        max_data (float): The maximum value of the data for the axis
            dimension.
        max_ticks (int): The maximum number of ticks.

    Attributes:
        tick_values (List[float]): The values of the ticks in ascending
            order.
        axis_power (int): The power of ten in a number.
        axis_subtractor (float): The number which will be subtracted
            from all axis values for display.
        tick_divisor_power (int): The power of ten all tick values will
            be divided by after being subtracted by the
            ``axis_subtractor.``
        tick_labels (List[str]): The tick labels in order.
        axis_subtractor_label (str): The axis subtractor label.
    """

    min_data: float
    max_data: float
    max_ticks: int

    def __post_init__(self) -> None:
        """Constructor."""
        self.tick_values = _get_tick_values(
            min_data=self.min_data, max_data=self.max_data, max_ticks=self.max_ticks
        )
        self.axis_power = _find_closest_prefix_power(self.tick_values[-1])
        self.axis_subtractor, self.tick_divisor_power = _get_axis_label_adjustors(
            self.tick_values
        )
        self.tick_labels = _make_tick_labels(
            self.tick_values,
            axis_subtractor=self.axis_subtractor,
            tick_divisor_power=self.tick_divisor_power,
        )
        self.axis_subtractor_label = (
            None
            if self.axis_subtractor == 0
            else (
                f"{self.axis_subtractor / self.axis_power:0.2f}"
                f"{_get_metric_prefix(self.axis_power)}"
            )
        )
        pass


def _find_closest_prefix_power(number: float) -> int:
    """Return the closest power associated with an SI prefix.

    Args:
        number (float): A number to find the prefix power
            for.

    Returns:
        int: The closest SI prefix power.
    """
    return max(min(math.floor(math.log10(number)) // 3 * 3, 24), -24)


def _get_axis_label_adjustors(tick_values: List[float]) -> Tuple[float, int]:
    """Return the tick divisor power and axis subtractor.

    All ticks labels will be subtracted by the axis subtractor, then
    divided by ten to the tick divisor power.

    Args:
        tick_values (List[float]): The tick values in ascending order.

    Returns:
        (Tuple) Two element tuple containing
        axis_subtractor (float): The number that will be subtracted
            from all axis tick labels.
        tick_divisor_power (int): The tens power to divide all tick
            labels by.
    """
    number_of_ticks = len(tick_values)
    axis_divisor_power = _find_closest_prefix_power(tick_values[-1])
    if number_of_ticks <= 1:
        tick_divisor_power = axis_divisor_power
        axis_subtractor = 0
    else:
        step_size = tick_values[1] - tick_values[0]
        step_place = math.floor(math.log10(step_size))
        if 2 < (axis_divisor_power - step_place):
            axis_range_place = math.floor(math.log10(tick_values[-1] - tick_values[0]))
            tick_place = (
                step_place if 2 < (axis_range_place - step_place) else axis_range_place
            )
            axis_subtractor = (tick_values[-1] // 10 ** (tick_place + 1)) * 10 ** (
                tick_place + 1
            )
            tick_divisor_power = _find_closest_prefix_power(10 ** tick_place)
        else:
            tick_divisor_power = axis_divisor_power
            axis_subtractor = 0
    return axis_subtractor, tick_divisor_power


def _get_metric_prefix(power: int, default: str = "") -> str:
    """Return the metric prefix for the power.

    Args:
        power (int): The power whose metric prefix will be returned.
        default (str): The default value to return if an exact match is
            not found.

    Returns:
        str: The metric prefix.
    """
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
    return metric_prefix.get(power, default)


def _make_tick_labels(
    tick_values: List[float], axis_subtractor: float, tick_divisor_power: int,
) -> List[str]:
    """Given a collection of ticks, return a formatted version.

    Args:
        tick_values (List[float]): The ticks positions in ascending
            order.
        tick_divisor_power (int): The power of ten the tick labels will
            be divided by.
        axis_subtractor (float): The amount to subtract from the tick
            values.

    Returns:
        Generator[str, None, None]: The generated tick labels.
    """
    tick_divisor_prefix = _get_metric_prefix(tick_divisor_power)
    return [
        f"{(tick - axis_subtractor) / 10 ** tick_divisor_power:0.2f}"
        f"{tick_divisor_prefix}"
        for tick in tick_values
    ]


def _round_number(
    number: float,
    limits: Tuple[float, ...],
    rounding_terms: Tuple[float, ...],
    allow_equal: bool,
) -> float:
    """Round a number to an intuitive form.

    Args:
        number (float): The number to round
        limits (Tuple[float, ...]): The associated rounding points
            in ascending order. The rounding term assigned to the
            number depends on where it is placed on the it will be
            rounded to the associated rounding points on
            ``rounding_terms``.
        rounding_terms (Tuple[float, ...]): The terms to round to if
            the number falls below or equal to the associated
            rounding points.
        allow_equal (bool): Whether to allow the number to be equal
            to the rounding points. If set False

    Returns:
        float: The number in a rounded form.
    """
    power = math.floor(math.log10(number))
    leading_term = number / 10 ** power
    limit_index = (
        bisect.bisect_left(limits, leading_term)
        if allow_equal
        else bisect.bisect_right(limits, leading_term)
    )
    rounded_lead = (
        10 if (len(limits) - 1) < limit_index else rounding_terms[limit_index]
    )
    return rounded_lead * 10.0 ** power


def _get_tick_values(min_data: float, max_data: float, max_ticks: int) -> List[float]:
    """Calculate the positions of the ticks.

    Args:
        min_data (float): The minimum value of the data for the axis
                dimension.
        max_data (float): The maximum value of the data for the axis
            dimension.
        max_ticks (int): The maximum number of ticks.

    Returns:
        List[float]: The tick positions in ascending order.
    """
    if max_data == min_data:
        return [min_data]
    else:
        data_range = max_data - min_data
        rounded_range = _round_number(
            data_range, limits=(1.5, 3, 7), rounding_terms=(1, 2, 5), allow_equal=False,
        )
        spacing = rounded_range / (max_ticks - 1)
        tick_spacing = _round_number(
            spacing, limits=(1, 2, 5), rounding_terms=(1, 2, 5), allow_equal=True
        )
        first_tick = math.floor(min_data / tick_spacing) * tick_spacing
        last_tick = math.ceil(max_data / tick_spacing) * tick_spacing
        number_of_ticks: int = math.ceil((last_tick - first_tick) / tick_spacing) + 1
        return [
            first_tick + factor * tick_spacing for factor in range(0, number_of_ticks)
        ]
