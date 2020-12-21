"""A unicode number line."""
import bisect
import dataclasses
import math
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import rich.columns
import rich.measure
import rich.table
import rich.text
from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.measure import Measurement
from rich.table import Column
from rich.text import Text
from typing_extensions import Literal


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
        if self.max_data < self.min_data:
            raise ValueError("min_data must be less than or equal to max_data")
        if self.max_ticks < 1:
            raise ValueError("max_ticks must be 1 or greater")
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
                f"{self.axis_subtractor / (10 ** self.axis_power):0.2f}"
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
    return (
        max(min(math.floor(math.log10(abs(number))) // 3 * 3, 24), -24)
        if number != 0
        else 0
    )


def _get_min_step_size(tick_values: List[float]) -> float:
    """Get the minimum step size given a list of tick vales.

    Tick values must be in ascending order.

    Args:
        tick_values (List[float]): The tick values in ascending order.

    Raises:
        ValueError: If ``tick_values`` are not found to be in ascending
            order.

    Returns:
        float
    """
    left_tick, right_tick = min(
        zip(tick_values[:-1], tick_values[1:]),
        key=lambda tick_pair: tick_pair[1] - tick_pair[0],
    )
    min_tick_step = right_tick - left_tick
    if min_tick_step < 0:
        raise ValueError(
            "Ticks must be in ascending order."
            f" {left_tick} is greater than {right_tick}"
        )
    # Round off in case of floating point errors
    elif min_tick_step != 0:
        min_tick_step_place = math.floor(math.log10(min_tick_step))
        next_place_up = 10 ** (min_tick_step_place + 1)
        if ((next_place_up - min_tick_step) / min_tick_step) < 0.001:
            min_tick_step = next_place_up
    return min_tick_step


def _get_axis_label_adjustors(tick_values: List[float]) -> Tuple[float, int]:
    """Return the tick divisor power and axis subtractor.

    All ticks labels will be subtracted by the axis subtractor, then
    divided by ten to the tick divisor power.

    Args:
        tick_values (List[float]): The tick values in ascending order.

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
        min_step_size = _get_min_step_size(tick_values)
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
            to the rounding points.

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

    Raises:
        ValueError: If ``max_ticks`` is less than 1.

    Returns:
        List[float]: The tick positions in ascending order.
    """
    if max_data == min_data:
        return [min_data]
    if max_ticks == 1:
        return [(min_data + max_data) / 2]
    if max_ticks <= 0:
        raise ValueError("max_ticks must be greater than 0")
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
        if max_ticks < number_of_ticks:
            first_tick = min_data
            number_of_ticks = max_ticks
            tick_spacing = data_range / (max_ticks - 1)
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
        min_tick_margin (int): The minimum spacing between ticks.
        width (int): The width of the axis in characters.
        tick_values (List[float], optional): The values for the ticks.
            By default will be automatically calculated.
        tick_labels (List[str], optional): The labels for the ticks.
            By default will be automatically calculated.
        characters (Dict[str, str]): The characters to use in creating
            the xline. Gets values from "xline", "xtick", and
            "xtick_spacing" keys.
        show_ticks (bool): Whether to show ticks on the xaxis. By
            default True.

    Attributes:
        width (int): The width of the x axis.
        tick_padding (int): The space on either side of the actual tick
            location. Considered to be a part of the tick.
        number_of_xticks (int): The number of x ticks.
        tick_margin (int): The spacing between ticks, not including the
            tick padding.
        left_padding (int): The spacing on the left of the x axis.
        right_padding (int): The spacing on the right of the x axis.
        tick_positions (List[int]): The locations of
            the actual ticks on the x line.
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
        table_columns (List[Column]): The columns that compose the x
            axis.
        characters (Dict[str, str]): The characters to use in creating
            the xline. Gets values from "xline", "xtick", and
            "xtick_spacing" keys.
        show_ticks (bool): Whether xticks are shown on the xaxis.
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
        characters: Optional[Dict[str, str]] = None,
        show_ticks: bool = True,
    ) -> None:
        """Constructor."""
        if any(
            measurement < 0 for measurement in (tick_padding, min_tick_margin, width)
        ):
            raise ValueError(
                "tick_padding, min_tick_margin, and width must be 0 or greater"
            )
        if width < (2 * tick_padding) + 1:
            raise ValueError(
                "tick_padding is too large and will not fit in allocated width."
            )
        self.width = width
        self.characters = characters or {}
        self.show_ticks = show_ticks
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
        total_tick_space = self.number_of_xticks * (self.tick_padding * 2 + 1)
        tick_margin = (
            (self.width - total_tick_space) // (self.number_of_xticks - 1)
            if 1 < self.number_of_xticks
            else 0
        )
        self.tick_margin = max(tick_margin, 0)
        total_taken_space = total_tick_space + (
            self.tick_margin * (self.number_of_xticks - 1)
        )
        extra_space = max(self.width - total_taken_space, 0)
        self.left_padding = extra_space // 2
        self.right_padding = max(extra_space - self.left_padding, 0)
        self.tick_positions = list(
            range(
                self.tick_padding + self.left_padding,
                self.width + 1,
                self.tick_margin + 2 * self.tick_padding + 1,
            )
        )
        self.table_columns = self._make_xaxis_columns(
            number_of_ticks=self.number_of_xticks,
            tick_padding=self.tick_padding,
            left_padding=self.left_padding,
            right_padding=self.right_padding,
            tick_margin=self.tick_margin,
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Console protocol for Rich."""
        xaxis_grid = rich.table.Table(
            *self.table_columns,
            width=self.width,
            box=None,
            collapse_padding=True,
            pad_edge=False,
            show_edge=False,
            show_footer=False,
            show_lines=False,
            show_header=False,
            padding=(0, 0),
        )
        xaxis_grid.add_row(*self.xline())
        xaxis_grid.add_row(*self.xtick_labels())
        yield xaxis_grid

    def __rich_measure__(self, console: Console, max_width: int) -> Measurement:
        """The width of the renderable."""
        return rich.measure.Measurement(minimum=self.width, maximum=max_width)

    def _make_xaxis_columns(
        self,
        number_of_ticks: int,
        tick_padding: int,
        left_padding: int,
        right_padding: int,
        tick_margin: int,
    ) -> List[Column]:
        """Create the columns that compose the x axis.

        Args:
            number_of_ticks (int): The number of ticks in the axis.
            tick_padding (int): The padding for the tick.
            left_padding (int): The padding on the left for the x axis.
            right_padding (int): The padding on the right for the x
                axis.
            tick_margin (int): The margin for the ticks.

        Returns:
            List[Column]: Columns that compose the x axis with
                corresponding widths.
        """
        xaxis_columns = [
            rich.table.Column(
                header="xtick",
                width=2 * tick_padding + 1,
                no_wrap=True,
                justify="center",
            )
            if column_number % 2 == 0
            else rich.table.Column(
                header="xtick_margin", width=tick_margin, no_wrap=True,
            )
            for column_number in range(2 * number_of_ticks - 1)
        ]
        xaxis_columns = (
            [
                rich.table.Column(
                    header="left_padding", width=left_padding, no_wrap=True,
                )
            ]
            + xaxis_columns
            + [
                rich.table.Column(
                    header="right_padding", width=right_padding, no_wrap=True,
                )
            ]
        )
        return xaxis_columns

    def xline(self) -> List[Text]:
        """Create the xline.

        Returns:
            Text: The xline row of the chart.
        """
        xline_character = self.characters.get("xline", "━")
        xtick_character = (
            self.characters.get("xtick", "┳") if self.show_ticks else xline_character
        )
        xline = []
        for column in self.table_columns:
            if column.header == "xtick":
                xline.append(
                    rich.text.Text.assemble(
                        rich.text.Text(
                            self.tick_padding * xline_character,
                            style="xaxis",
                            overflow="crop",
                        ),
                        rich.text.Text(
                            xtick_character, style="xtick_label", overflow="crop"
                        ),
                        rich.text.Text(
                            self.tick_padding * xline_character,
                            style="xaxis",
                            overflow="crop",
                        ),
                    )
                )
            elif column.header == "left_padding":
                xline.append(
                    rich.text.Text(
                        xline_character * self.left_padding,
                        style="xaxis",
                        overflow="crop",
                    )
                )
            elif column.header == "right_padding":
                xline.append(
                    rich.text.Text(
                        xline_character * self.right_padding,
                        style="xaxis",
                        overflow="crop",
                    )
                )
            else:
                xline.append(
                    rich.text.Text(
                        xline_character * self.tick_margin,
                        style="xaxis",
                        overflow="crop",
                    )
                )
        return xline

    def xtick_labels(self) -> List[Text]:
        """Create the xlabels.

        Returns:
            Text: The xlabel row of the chart.
        """
        xtick_spacing_character = self.characters.get("xtick_spacing", " ")
        xtick_labels = []
        tick_labels = self.tick_labels.copy() if self.tick_labels else []
        for column in self.table_columns:
            if column.header == "xtick":
                xtick_labels.append(
                    rich.text.Text(
                        tick_labels.pop(0),
                        style="xtick_label",
                        overflow="ellipsis",
                        justify="center",
                    )
                )
            elif column.header == "left_padding":
                xtick_labels.append(
                    rich.text.Text(
                        xtick_spacing_character * self.left_padding,
                        style="xtick_spacing",
                        overflow="crop",
                    )
                )
            elif column.header == "right_padding":
                xtick_labels.append(
                    rich.text.Text(
                        xtick_spacing_character * self.right_padding,
                        style="xtick_spacing",
                        overflow="crop",
                    )
                )
            else:
                xtick_labels.append(
                    rich.text.Text(
                        xtick_spacing_character * self.tick_margin,
                        style="xtick_spacing",
                        overflow="crop",
                    )
                )
        return xtick_labels


class YAxis(Ticks):
    """YAxis.

    Args:
        min_data (float): The minimum value of the data for the axis
            dimension
        max_data (float): The maximum value of the data for the axis
            dimension.
        min_tick_margin (int): The minimum spacing between ticks.
        length (int): The length of the axis in characters.
        width (int): The width of the axis in characters.
        position (Literal["left", "right"]): Whether the axis is to
            appear on the left or right side of the chart. By default
            "right".
        tick_values (List[float], optional): The values for the ticks.
            By default will be automatically calculated.
        tick_labels (List[str], optional): The labels for the ticks.
            By default will be automatically calculated.
        characters (Dict[str, str]): The characters to use in
            creating the xline. Gets values from "yline", "left_ytick",
            and "right_ytick" keys.
        show_ticks (bool): Whether to show ticks on the yaxis. By
            default True.

    Attributes:
        length (int): The length of the axis in characters.
        characters (Dict[str, str]): The characters to use in creating
            the xline. Gets values from "yline", "left_ytick",
            "right_ytick", and "ytick_spacing" keys.
        number_of_yticks (int)
        tick_margin (int)
        top_padding (int)
        bottom_padding (int)
        tick_positions (List[int])
        table_columns (List[Column]): The columns that compose the y
            axis.
        show_ticks (bool): Whether xticks are shown on the xaxis.
    """

    def __init__(
        self,
        min_data: float,
        max_data: float,
        min_tick_margin: int,
        length: int,
        width: int,
        position: Literal["left", "right"] = "right",
        tick_values: Optional[List[float]] = None,
        tick_labels: Optional[List[str]] = None,
        characters: Optional[Dict[str, str]] = None,
        show_ticks: bool = True,
    ) -> None:
        """Constructor."""
        if position in ("left", "right"):
            self.position = position
        else:
            raise ValueError("position must be 'left' or 'right'")
        if any(measurement < 0 for measurement in (min_tick_margin, width, length)):
            raise ValueError("min_tick_margin, width, and length must be 0 or greater")
        self.width = width
        self.length = length
        self.show_ticks = show_ticks
        self.characters = characters or {}
        max_ticks = 1 + ((self.length - 1) // (1 + min_tick_margin))
        super().__init__(
            min_data=min_data,
            max_data=max_data,
            max_ticks=max_ticks,
            tick_values=tick_values,
            tick_labels=tick_labels,
        )
        self.number_of_yticks = len(self.tick_values) if self.tick_values else 0
        tick_margin = (
            (self.length - self.number_of_yticks) // (self.number_of_yticks - 1)
            if 1 < self.number_of_yticks
            else 0
        )
        print(tick_margin)
        self.tick_margin = max(tick_margin, 0)
        total_taken_space = self.number_of_yticks + (
            self.tick_margin * (self.number_of_yticks - 1)
        )
        print(total_taken_space)
        extra_space = max(self.length - total_taken_space, 0)
        self.top_padding = extra_space // 2
        self.bottom_padding = max(extra_space - self.top_padding, 0)
        print(self.top_padding, self.bottom_padding)
        self.tick_positions = list(
            range(self.top_padding, self.length + 1, self.tick_margin + 1)
        )
        self.table_columns = self._make_yaxis_columns()

    def _make_yaxis_columns(self) -> List[Column]:
        """Create the columns that compose the y axis."""
        ytick_column = rich.table.Column(
            header="ytick", width=1, no_wrap=True, justify="left", overflow="crop",
        )
        label_column = rich.table.Column(
            header="ytick_label",
            width=self.width - 1,
            no_wrap=True,
            justify="left",
            overflow="ellipsis",
        )
        yaxis_columns = (
            [label_column, ytick_column]
            if self.position == "left"
            else [ytick_column, label_column]
        )
        return yaxis_columns

    def yline(self) -> List[Text]:
        """Create the yline.

        Returns:
            Text: The xline row of the chart.
        """
        yline_character = self.characters.get("yline", "┃")
        if not self.show_ticks:
            ytick_character = yline_character
        elif self.position == "left":
            ytick_character = self.characters.get("left_tick", "┫")
        else:
            ytick_character = self.characters.get("right_ytick", "┣")
        tick_positions = set(self.tick_positions)
        yline = [
            rich.text.Text(ytick_character, style="ytick")
            if row in tick_positions
            else rich.text.Text(yline_character, style="yaxis")
            for row in range(self.top_padding, self.length - self.bottom_padding)
        ]
        yline = (
            self.top_padding * [rich.text.Text(yline_character, style="yaxis")]
            + yline
            + self.bottom_padding * [rich.text.Text(yline_character, style="yaxis")]
        )
        print(yline)
        print(tick_positions)
        print(self.top_padding)
        return yline

    def ytick_labels(self) -> List[Text]:
        """Create the ylabels.

        Returns:
            List[Text]: The y tick labels from top to bottom.
        """
        ytick_spacing_character = self.characters.get("ytick_spacing", " ")
        label_width = self.width - 1
        ytick_labels = self.top_padding * [
            rich.text.Text(
                ytick_spacing_character, style="ytick_spacing", overflow="crop"
            )
        ]
        tick_labels = self.tick_labels.copy() if self.tick_labels else []
        leftover: Union[None, str] = None
        tick_positions = set(self.tick_positions)
        for row in range(self.top_padding, self.length - self.bottom_padding):
            if row in tick_positions or leftover:
                full_label = leftover or tick_labels.pop(-1)
                if label_width < len(full_label) and (row + 1) not in tick_positions:
                    label = full_label[:label_width]
                    leftover = full_label[label_width:]
                else:
                    label = full_label
                    leftover = None
                ytick_labels.append(
                    rich.text.Text(label, style="ytick_label", overflow="ellipsis")
                )
            else:
                ytick_labels.append(
                    rich.text.Text(
                        ytick_spacing_character, style="ytick_spacing", overflow="crop"
                    )
                )
        ytick_labels += self.bottom_padding * [
            rich.text.Text(
                ytick_spacing_character, style="ytick_spacing", overflow="crop"
            )
        ]
        return ytick_labels
