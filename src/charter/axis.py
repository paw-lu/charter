"""A unicode number line."""
import bisect
import dataclasses
import math
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import rich.text
from rich.text import Text


@dataclasses.dataclass()
class Ticks:
    """Chart ticks.

    Args:
        min_data (float): The minimum value of the data for the axis
                dimension.
        max_data (float): The maximum value of the data for the axis
            dimension.
        max_ticks (int): The maximum number of ticks.
        tick_values (Optional[List[float]]): The tick values.
        tick_labels (Optional[List[str]]): The tick labels.

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
    tick_values: Optional[List[float]] = None
    tick_labels: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Constructor."""
        self.tick_values = self.tick_values or _get_tick_values(
            min_data=self.min_data, max_data=self.max_data, max_ticks=self.max_ticks
        )
        self.axis_power = _find_closest_prefix_power(self.tick_values[-1])
        self.axis_subtractor, self.tick_divisor_power = _get_axis_label_adjustors(
            self.tick_values
        )
        self.tick_labels = self.tick_labels or _make_tick_labels(
            self.tick_values,
            axis_subtractor=self.axis_subtractor,
            tick_divisor_power=self.tick_divisor_power,
        )
        if len(self.tick_values) != len(self.tick_labels):
            raise ValueError(
                f"{len(self.tick_values)} ticks and"
                f" {len(self.tick_labels)} tick labels were provided."
                " They should be equal."
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
        number (float): A number to find the prefix power for.

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

    Raises:
        ValueError: If ``tick_values`` are not found to be in ascending
            order.

    Returns:
        (Tuple) Two element tuple containing
        axis_subtractor (float): The number that will be subtracted from
            all axis tick labels.
        tick_divisor_power (int): The tens power to divide all tick
            labels by.
    """
    number_of_ticks = len(tick_values)
    axis_divisor_power = _find_closest_prefix_power(tick_values[-1])
    if number_of_ticks <= 1:
        tick_divisor_power = axis_divisor_power
        axis_subtractor = 0
    else:
        min_step_size = min(
            next_tick - tick for next_tick, tick in zip(tick_values[1:], tick_values)
        )
        if min_step_size < 0:
            raise ValueError(
                f"A step was found to be {min_step_size}."
                " tick_values should be in ascending order."
            )
        step_place = math.floor(math.log10(min_step_size))
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


class XAxis(Ticks):
    """XAxis.

    Args:
        min_data (float): The minimum value of the data for the axis
                dimension.
        max_data (float): The maximum value of the data for the axis
            dimension.
        tick_padding (int): The width a tick and its label takes up.
        tick_margin (int): The minimum spacing between ticks.
        width (int): The width of the axis in characters.
        tick_values (List[float], optional): The values for the ticks.
            By default will be automatically calculated.
        tick_labels (List[float], optional): The labels for the ticks.
            By default will be automatically calculated.

    Attributes:
        tick_values (List[float]): The positions of
            the ticks in ascending order.
        tick_labels (List[str]): The tick labels in ascending order.
    """

    def __init__(
        self,
        min_data: float,
        max_data: float,
        tick_padding: int,
        min_tick_margin: int,
        width: int,
        tick_values: Optional[List[float]] = None,
        tick_labels: Optional[List[str]] = None,
    ) -> None:
        """Constructor."""
        self.width = width
        max_ticks = 1 + (
            (self.width - (2 * tick_padding + 1))
            // ((2 * tick_padding + 1) + min_tick_margin)
        )
        super().__init__(
            min_data=min_data,
            max_data=max_data,
            max_ticks=max_ticks,
            tick_values=tick_values,
            tick_labels=tick_labels,
        )
        self.tick_padding = tick_padding
        self.number_of_xticks = len(self.tick_values) if self.tick_values else 0
        tick_margin = (
            self.width - (self.number_of_xticks * (self.tick_padding * 2 + 1))
        ) // (self.number_of_xticks - 1)
        self.tick_margin = max(tick_margin, 0)
        self.tick_positions = range(
            self.tick_padding,
            self.width + 1,
            self.tick_margin + 2 * self.tick_padding + 1,
        )

    def xline(self, characters: Dict[str, str], show_ticks: bool = True) -> Text:
        """Create the xline.

        Args:
            characters (Dict[str, str]): The characters to use in
                creating the xline. Gets values from "xline" and "xtick"
                keys.
            show_ticks (bool): Whether to show ticks on the xline.
                Defaults to True.

        Returns:
            Text: The xline row of the chart.
        """
        xline_character = characters.get("xline", "━")
        xtick_character = (
            characters.get("xtick", "┳") if show_ticks else xline_character
        )
        tick_positions = set(self.tick_positions)
        xline = rich.text.Text.assemble(
            *(
                rich.text.Text(xtick_character, style="xtick")
                if position in tick_positions
                else rich.text.Text(xline_character, style="xaxis")
                for position in range(0, self.width)
            )
        )
        return xline

    def xtick_labels(self, characters: Dict[str, str]) -> Text:
        """Create the xlabels.

        Args:
            characters (Dict[str, str]): The characters to use in
                creating the xline. Gets values from "xtick_spacing"
                keys.

        Returns:
            Text: The xlabel row of the chart.
        """
        xtick_spacing_character = characters.get("xtick_spacing", " ")
        xtick_labels = rich.text.Text()
        tick_positions = list(self.tick_positions)
        tick_labels = self.tick_labels.copy() if self.tick_labels else []
        position = 0
        tick_label = tick_labels.pop(0)
        upcoming_tick_position = tick_positions.pop(0) - (len(tick_label) // 2)
        while position <= self.width:
            if position == upcoming_tick_position:
                xtick_labels.append_text(
                    rich.text.Text(tick_label, style="xtick_label")
                )
                position += max(len(tick_label), 1)
                if tick_labels and tick_positions:
                    tick_label = tick_labels.pop(0)
                    upcoming_tick_position = tick_positions.pop(0) - (
                        len(tick_label) // 2
                    )
            else:
                xtick_labels.append_text(
                    rich.text.Text(xtick_spacing_character, style="xtick_spacing")
                )
                position += max(len(xtick_spacing_character), 1)
        return xtick_labels
