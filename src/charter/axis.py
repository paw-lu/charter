"""A unicode number line."""
import bisect
import math
from typing import List
from typing import Sequence
from typing import Tuple


class Ticks:
    """Chart ticks.

    Args:
        min_data (float): The minimum value of the data for the axis
                dimension.
        max_data (float): The maximum value of the data for the axis
            dimension.
        max_ticks (int): The maximum number of ticks.

    Attributes:
        tick_positions (List[float]): The positions of
            the ticks in ascending order.
        tick_labels (List[str]): The tick labels in ascending order.
    """

    def __init__(self, min_data: float, max_data: float, max_ticks: int) -> None:
        """Constructor."""
        self.tick_positions = self._make_tick_positions(
            min_data=min_data, max_data=max_data, max_ticks=max_ticks
        )
        self.tick_labels = self._make_tick_labels(tick_positions=self.tick_positions)
        pass

    def __repr__(self) -> str:
        """Representation of the Tick class."""
        return (
            f"Ticks(tick_positions={tuple(self.tick_positions)},"
            f" tick_labels={tuple(self.tick_labels)})"
        )

    def _find_closest_prefix_power(self, number: float) -> int:
        """Return the closest power associated with an SI prefix.

        Args:
            number (float): A number to find the prefix power
                for.

        Returns:
            int: The closest SI prefix power.
        """
        return max(min(int(math.log10(number) // 3 * 3), 24), -24)

    def _make_tick_labels(self, tick_positions: Sequence[float]) -> List[str]:
        """Given a collection of ticks, return a formatted version.

        Args:
            tick_positions (Sequence[float]): Equally spaced tick
                positions in ascending order for which the labels will
                be generated for.

        Raises:
            TypeError: If ticks are not numerical.

        Returns:
            Generator[str, None, None]: The generated tick labels.
        """
        if any(
            not isinstance(tick_position, (int, float))
            for tick_position in tick_positions
        ):
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
        first_tick_position = tick_positions[0]
        second_tick_position = tick_positions[1]
        step_size = second_tick_position - first_tick_position
        axis_divisor_power = self._find_closest_prefix_power(tick_positions[-1])
        axis_prefix = metric_prefix.get(axis_divisor_power, "")
        step_place = math.log10(step_size)
        number_of_ticks = len(tick_positions)
        if 2 < (axis_divisor_power - math.floor(step_place)):
            tick_divisor_power = self._find_closest_prefix_power(step_size)
            tick_divisor_prefix = metric_prefix.get(tick_divisor_power, "")
            return [
                f"{(tick - 10 ** axis_divisor_power) / 10 ** tick_divisor_power:0.2f}"
                f"{tick_divisor_prefix}"
                + (i == number_of_ticks - 1) * f" + 1{axis_prefix}"
                for i, tick in enumerate(tick_positions)
            ]
        else:
            return [
                f"{tick / 10 ** axis_divisor_power :0.2f}"
                + (i == number_of_ticks - 1) * axis_prefix
                for i, tick in enumerate(tick_positions)
            ]

    def _round_number(
        self,
        number: float,
        limits: Tuple[float, ...],
        rounding_terms: Tuple[float, ...],
        allow_equal: bool,
    ) -> float:
        """Round a number to a intuitive form.

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

    def _make_tick_positions(
        self, min_data: float, max_data: float, max_ticks: int
    ) -> List[float]:
        """Calculate the positions of the ticks.

        Args:
            min_data (float): The minimum value of the data for the axis
                dimension.
            max_data (float): The maximum value of the data for the axis
                dimension.
            max_ticks (int): The maximum number of ticks that may be
                used.

        Returns:
            List[float]: The tick positions in ascending order.
        """
        if max_data == min_data:
            return [min_data]
        else:
            data_range = max_data - min_data
            rounded_range = self._round_number(
                data_range,
                limits=(1.5, 3, 7),
                rounding_terms=(1, 2, 5),
                allow_equal=False,
            )
            spacing = rounded_range / (max_ticks - 1)
            tick_spacing = self._round_number(
                spacing, limits=(1, 2, 5), rounding_terms=(1, 2, 5), allow_equal=True
            )
            first_tick = math.floor(min_data / tick_spacing) * tick_spacing
            last_tick = math.ceil(max_data / tick_spacing) * tick_spacing
            number_of_ticks: int = math.ceil(
                (last_tick - first_tick) / tick_spacing
            ) + 1
            return [
                first_tick + factor * tick_spacing
                for factor in range(0, number_of_ticks)
            ]
