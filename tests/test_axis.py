"""Test the number line generator."""
import io
from typing import Dict
from typing import List
from typing import Tuple

import hypothesis
import hypothesis.strategies as st
import pytest
import rich.console
import rich.table
import rich.text
from typing_extensions import Literal

from charter import axis


def test_xaxis_console_render() -> None:
    """It renders an x axis."""
    width = 80
    console = rich.console.Console(file=io.StringIO(), width=width)
    console.print(
        axis.XAxis(
            min_data=15, max_data=150, tick_padding=3, min_tick_margin=2, width=width
        )
    )
    output = console.file.getvalue()  # type: ignore[attr-defined]
    assert output == (
        " ━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━"
        "━━━━━┳━━━━━━━━┳━━━\n  0.00     20.00    40.00    60.00"
        "    80.00   100.00   120.00   140.00   160.00 \n"
    )


def test_xaxis_rich_measure() -> None:
    """It's min width measures the axis' width."""
    width = 80
    xaxis = axis.XAxis(
        min_data=15, max_data=150, tick_padding=3, min_tick_margin=2, width=width
    )
    console = rich.console.Console()
    min_width, _ = xaxis.__rich_measure__(console=console, max_width=100)
    assert min_width == width


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
        ([-1e6 + 1, -1e6 + 2, -1e6 + 3], -1e6, 0),
        ([step / 100 for step in range(0, 101)], 0, 0),
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


def test_not_ascending_order() -> None:
    """It raises a ValueError if ticks aren't in ascending order."""
    with pytest.raises(ValueError):
        axis._get_axis_label_adjustors([1, 2, 3, 6, 5])


@pytest.mark.parametrize(
    "characters, show_ticks",
    [({"xline": "━", "xtick": "┳"}, True), ({"xline": "-", "xtick": "|"}, False,)],
)
def test_xline(characters: Dict[str, str], show_ticks: bool) -> None:
    """It creates the x line."""
    xaxis = axis.XAxis(
        min_data=0,
        max_data=10,
        tick_padding=3,
        min_tick_margin=1,
        width=24,
        tick_values=None,
        tick_labels=None,
        characters=characters,
        show_ticks=show_ticks,
    )
    actual_xline = xaxis.xline()
    tick_padding = rich.text.Text(
        characters["xline"] * 3, style="xaxis", overflow="crop"
    )
    xtick_section = rich.text.Text.assemble(
        tick_padding,
        rich.text.Text(
            characters["xtick"] if show_ticks else characters["xline"],
            style="xtick_label",
            overflow="crop",
        ),
        tick_padding,
    )
    margin_section = rich.text.Text(characters["xline"], style="xaxis", overflow="crop")
    expected_xline = [
        rich.text.Text("", style="xaxis", overflow="crop"),
        xtick_section,
        margin_section,
        xtick_section,
        margin_section,
        xtick_section,
        rich.text.Text(characters["xline"], style="xaxis", overflow="crop"),
    ]
    assert actual_xline == expected_xline


def test_xtick_labels() -> None:
    """It creates the x tick labels."""
    xaxis = axis.XAxis(
        min_data=0,
        max_data=10,
        tick_padding=3,
        min_tick_margin=1,
        width=24,
        tick_values=None,
        tick_labels=None,
        characters={"xtick_spacing": "_"},
    )
    actual_xtick_lables = xaxis.xtick_labels()
    expected_xtick_labels = [
        rich.text.Text("", style="xtick_spacing", overflow="crop"),
        rich.text.Text(
            "0.00", style="xtick_label", overflow="ellipsis", justify="center"
        ),
        rich.text.Text("_", style="xtick_spacing", overflow="crop"),
        rich.text.Text(
            "5.00", style="xtick_label", overflow="ellipsis", justify="center"
        ),
        rich.text.Text("_", style="xtick_spacing", overflow="crop"),
        rich.text.Text(
            "10.00", style="xtick_label", overflow="ellipsis", justify="center"
        ),
        rich.text.Text("_", style="xtick_spacing", overflow="crop"),
    ]
    assert actual_xtick_lables == expected_xtick_labels


def test_min_larger_max_xaxis() -> None:
    """It raises a ValueError is min_data is larger than max_data."""
    with pytest.raises(ValueError):
        axis.XAxis(min_data=10, max_data=4, tick_padding=3, min_tick_margin=1, width=10)


def test_negative_measurements() -> None:
    """It raises a ValueError if measurements are negative."""
    with pytest.raises(ValueError):
        axis.XAxis(
            min_data=10, max_data=4, tick_padding=3, min_tick_margin=1, width=-10
        )


def test_no_axis_subtractor() -> None:
    """It returns no label if there is nothing to subtract."""
    xaxis = axis.XAxis(
        min_data=0, max_data=1, tick_padding=0, min_tick_margin=0, width=101
    )
    assert xaxis.axis_subtractor_label is None


def test_min_step_zero() -> None:
    """It returns a min step size of 0 when two ticks are equal."""
    actual_min_step_size = axis._get_min_step_size([10, 10])
    assert actual_min_step_size == 0


def test_raise_exception_zero_max_tick() -> None:
    """It raises a ValueError is the max_tick it too low."""
    with pytest.raises(ValueError):
        axis.Ticks(min_data=4, max_data=10, max_ticks=0)


def test_max_ticks_one() -> None:
    """It returns the midpoint as a tick value if max_ticks is 1."""
    ticks = axis.Ticks(min_data=0, max_data=10, max_ticks=1)
    assert ticks.tick_values == [5]


def test_raise_exception_zero_max_tick_value() -> None:
    """It raises a ValueError is the max_tick is too low."""
    with pytest.raises(ValueError):
        axis._get_tick_values(min_data=0, max_data=10, max_ticks=0)


def test_raises_padding_too_big() -> None:
    """It raises a ValueError when the tick padding is too large."""
    with pytest.raises(ValueError):
        axis.XAxis(
            min_data=0, max_data=10, tick_padding=3_000, min_tick_margin=2, width=4
        )


def test_fallback_ticks() -> None:
    """It will fallback to a simple algorithm when the range is low."""
    xaxis = axis.XAxis(
        min_data=0, max_data=6, tick_padding=0, min_tick_margin=0, width=2
    )
    assert xaxis.tick_values == [0.0, 6.0]


@hypothesis.given(
    min_data=st.integers(min_value=-999_999, max_value=999_999),
    max_data=st.integers(min_value=-999_999, max_value=999_999),
    tick_padding=st.integers(min_value=0),
    min_tick_margin=st.integers(min_value=0),
    width=st.integers(min_value=0, max_value=999_999),
)
@hypothesis.settings(deadline=1_000)  # type: ignore[misc]
@hypothesis.example(min_data=0, max_data=0, tick_padding=0, min_tick_margin=0, width=0)
def test_tick_creation_hypothesis(
    min_data: int, max_data: int, tick_padding: int, min_tick_margin: int, width: int
) -> None:
    """It creates at at least one tick given any valid data."""
    hypothesis.assume(min_data <= max_data)
    hypothesis.assume((2 * tick_padding) < width)
    xaxis = axis.XAxis(
        min_data=min_data,
        max_data=max_data,
        tick_padding=tick_padding,
        min_tick_margin=min_tick_margin,
        width=width,
    )
    assert 1 <= xaxis.number_of_xticks


@hypothesis.given(
    min_data=st.integers(min_value=-999_999, max_value=999_999),
    max_data=st.integers(min_value=-999_999, max_value=999_999),
    tick_padding=st.integers(min_value=0),
    min_tick_margin=st.integers(min_value=0),
    width=st.integers(min_value=2, max_value=999_999),
)
@hypothesis.settings(deadline=1_000)  # type: ignore[misc]
@hypothesis.example(min_data=0, max_data=6, tick_padding=0, min_tick_margin=0, width=2)
@hypothesis.example(min_data=-1, max_data=1, tick_padding=0, min_tick_margin=0, width=2)
@hypothesis.example(min_data=0, max_data=0, tick_padding=1, min_tick_margin=0, width=2)
def test_axis_width_hypothesis(
    min_data: int, max_data: int, tick_padding: int, min_tick_margin: int, width: int
) -> None:
    """The width of the table created matches the available width."""
    hypothesis.assume(min_data <= max_data)
    hypothesis.assume((2 * tick_padding) < width)
    xaxis = axis.XAxis(
        min_data=min_data,
        max_data=max_data,
        tick_padding=tick_padding,
        min_tick_margin=min_tick_margin,
        width=width,
    )
    table_width = sum(column.width for column in xaxis.table_columns)
    assert table_width == width


@pytest.mark.parametrize(
    "min_tick_margin, width, length", [(-1, 0, 0), (0, -1, 0), (0, 0, -1)]
)
def test_raises_value_error_on_negative(
    min_tick_margin: int, width: int, length: int
) -> None:
    """It raises a ValueError when measurement values are negative."""
    with pytest.raises(ValueError):
        axis.YAxis(
            min_data=0,
            max_data=10,
            min_tick_margin=min_tick_margin,
            length=length,
            width=width,
        )


def test_raises_value_error_on_bad_position() -> None:
    """It raises a ValueError if the position is not valid."""
    with pytest.raises(ValueError):
        axis.YAxis(
            min_data=0,
            max_data=10,
            min_tick_margin=2,
            length=50,
            width=10,
            position="bad value",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("position", ["left", "right"])
def test_columns_reorient(position: Literal["left", "right"]) -> None:
    """It reorients its columns based on the position argument."""
    width = 10
    yaxis = axis.YAxis(
        min_data=0,
        max_data=10,
        min_tick_margin=2,
        length=50,
        width=10,
        position=position,
    )
    ytick_column = rich.table.Column(
        header="ytick", width=1, no_wrap=True, justify="left", overflow="crop",
    )
    label_column = rich.table.Column(
        header="ytick_label",
        width=width - 1,
        no_wrap=True,
        justify="left",
        overflow="ellipsis",
    )
    expected_columns = (
        [label_column, ytick_column]
        if position == "left"
        else [ytick_column, label_column]
    )
    assert yaxis.table_columns == expected_columns


def test_ytick_labels() -> None:
    """It creates y labels."""
    yaxis = axis.YAxis(
        min_data=0, max_data=5, min_tick_margin=2, length=5, width=10, position="left",
    )
    expected_ytick_labels = (
        [rich.text.Text("5.00", style="ytick_label", overflow="ellipsis")]
        + 3 * [rich.text.Text(" ", style="ytick_spacing", overflow="crop")]
        + [rich.text.Text("0.00", style="ytick_label", overflow="ellipsis")]
    )
    assert yaxis.ytick_labels() == expected_ytick_labels


def test_ytick_labels_characters() -> None:
    """It uses the provided characters when drawing the y labels."""
    yaxis = axis.YAxis(
        min_data=0,
        max_data=5,
        min_tick_margin=2,
        length=5,
        width=10,
        position="left",
        characters={"ytick_spacing": "q"},
    )
    expected_ytick_labels = (
        [rich.text.Text("5.00", style="ytick_label", overflow="ellipsis")]
        + 3 * [rich.text.Text("q", style="ytick_spacing", overflow="crop")]
        + [rich.text.Text("0.00", style="ytick_label", overflow="ellipsis")]
    )
    assert yaxis.ytick_labels() == expected_ytick_labels


def test_yline() -> None:
    """It creates the y line."""
    yaxis = axis.YAxis(
        min_data=0, max_data=5, min_tick_margin=2, length=5, width=10, position="left",
    )
    ytick = rich.text.Text("┫", style="ytick")
    yline = rich.text.Text("┃", style="yaxis")
    expected_yline = [ytick] + 3 * [yline] + [ytick]
    assert yaxis.yline() == expected_yline


def test_yline_characters() -> None:
    """It uses the provided characters when drawing the y line."""
    yaxis = axis.YAxis(
        min_data=0,
        max_data=5,
        min_tick_margin=2,
        length=5,
        width=10,
        position="left",
        characters={"yline": "a", "left_tick": "b"},
    )
    ytick = rich.text.Text("b", style="ytick")
    yline = rich.text.Text("a", style="yaxis")
    expected_yline = [ytick] + 3 * [yline] + [ytick]
    assert yaxis.yline() == expected_yline


def test_yline_right() -> None:
    """It uses the right character when positioned on the right."""
    yaxis = axis.YAxis(
        min_data=0, max_data=5, min_tick_margin=2, length=5, width=10, position="right",
    )
    ytick = rich.text.Text("┣", style="ytick")
    yline = rich.text.Text("┃", style="yaxis")
    expected_yline = [ytick] + 3 * [yline] + [ytick]
    assert yaxis.yline() == expected_yline


def test_yline_no_ticks() -> None:
    """It doesn't draw ticks when show_ticks is set to False."""
    yaxis = axis.YAxis(
        min_data=0,
        max_data=5,
        min_tick_margin=2,
        length=5,
        width=10,
        position="right",
        show_ticks=False,
    )
    assert yaxis.yline() == 5 * [rich.text.Text("┃", style="yaxis")]


def test_long_labels() -> None:
    """It overflows tick labels to the next line if needed."""
    yaxis = axis.YAxis(
        min_data=0,
        max_data=5,
        min_tick_margin=2,
        length=5,
        width=3,
        position="right",
        tick_labels=["zzyyxx", "aabbccddee"],
    )
    expected_ylabels = [
        rich.text.Text("aa", style="ytick_label", overflow="ellipsis"),
        rich.text.Text("bb", style="ytick_label", overflow="ellipsis"),
        rich.text.Text("cc", style="ytick_label", overflow="ellipsis"),
        rich.text.Text("ddee", style="ytick_label", overflow="ellipsis"),
        rich.text.Text("zzyyxx", style="ytick_label", overflow="ellipsis"),
    ]
    assert yaxis.ytick_labels() == expected_ylabels


def test_yaxis_rich_measure() -> None:
    """It's min width measures the y axis' width."""
    width = 5
    yaxis = axis.YAxis(
        min_data=15, max_data=150, min_tick_margin=2, width=width, length=30
    )
    console = rich.console.Console()
    min_width, _ = yaxis.__rich_measure__(console=console, max_width=100)
    assert min_width == width


def test_yaxis_console_render() -> None:
    """It renders a y axis."""
    width = 7
    console = rich.console.Console(file=io.StringIO(), width=width)
    console.print(
        axis.YAxis(min_data=15, max_data=150, min_tick_margin=2, width=width, length=5)
    )
    output = console.file.getvalue()  # type: ignore[attr-defined]
    assert output == "┣150.00\n┃      \n┃      \n┃      \n┣15.00 \n"
