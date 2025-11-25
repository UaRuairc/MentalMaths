import streamlit as st
from src.ui.widgets.registry import WidgetRegistry
from src.game.content.problem_engine import Question
from src.utils import get_range


def update_duration_box_on_change():
    choice_ = st.session_state["config"]["segmented_control"]["duration"]["value"]
    if choice_ is not None and choice_ != 3:
        st.session_state["config"]["number_input_box"]["duration"]["value"] = 30 * (2 ** choice_)

    if choice_ is None:
        st.session_state["config"]["number_input_box"]["duration"]["value"] = None

def update_disabled_boxes_on_change(type_, disabled_box):
    def wrapper():
        min_, max_ = Question.calc_theoretical_range(
            type_=type_[:-5],
            ranges_=lambda: get_range(type_),
            pos_answers_only=lambda: WidgetRegistry.get_widget_value("pos_answers_only", "checkbox"))

        WidgetRegistry.set_widget_value(f"{type_}_{disabled_box}_min", "number_input_box", min_)
        WidgetRegistry.set_widget_value(f"{type_}_{disabled_box}_max", "number_input_box", max_)

    return wrapper


OPERATOR_SYMBOLS =  {
            "add": r"$+$",
            "subtract": r"$-$",
            "mult": r"$\times$",
            "div": r"$\div$",
        }

PROBLEM_TYPE_INDEX_MAP = {
            0: {"operation": "add", "dtype": "ints"},
            1: {"operation": "subtract", "dtype": "ints"},
            2: {"operation": "mult", "dtype": "ints"},
            3: {"operation": "div", "dtype": "ints"},
            }

OPERATORS = ["add", "subtract", "mult", "div"]

SEGMENTED_CONTROL_OPTIONS = {
    "problem_types": {
        0: r"$+$",
        1: r"$-$",
        2: r"$\times$",
        3: r"$\div$"
    },
    "duration": {
        0: "30",
        1: "60",
        2: "120",
        3: "..."
    }
}

DEFAULT_DURATION_INDEX = 2

WIDGET_CALLABLES = {
    "streamlit": {
        "checkbox": st.checkbox,
        "slider": st.slider,
        "number_input_box": st.number_input,
        "segmented_control": st.segmented_control,
        "text_input_boxes": st.text_input,
        "buttons": st.button,
    },
    # Custom widgets imported lazily to avoid circular dependencies
    "custom": {}
}

def _init_custom_widgets():
    from src.ui.widgets.widgets import custom_input
    WIDGET_CALLABLES["custom"]["number_input_box"] = custom_input

DEFAULT_WIDGETS_V_01 = {

        "checkbox": {
            "add_ints": {"label": "addition"},
            "subtract_ints": {"label": "subtraction"},
            "mult_ints": {"label": "multiplication"},
            "div_ints": {"label": "division"},
            "pos_answers_only": {"label": "positive answers only?"},
            "fade_problem": {"label": "fade problem after set number of seconds?"},
        },
        "slider": {
            "add_ints_left": "left digit range",
            "subtract_ints_left": "left digit range",
            "mult_ints_left": "left digit range",
            "div_ints_left": "divisor range",
            "add_ints_right": "right digit range",
            "subtract_ints_right": "right digit range",
            "mult_ints_right": "right digit range",
            "div_ints_right": "quotient range",
            **{f"{op}_ints_{side}":
                {
                    "label": f"{side} digit range",
                    "min_value": 1,
                    "max_value": 200,
                    "value": (1, 9),
                }
               for op in OPERATORS for side in ["left", "right"]}
        },

        "segmented_control": {
            "duration": {
                "options": SEGMENTED_CONTROL_OPTIONS["duration"],
                "value": DEFAULT_DURATION_INDEX,
                "format_func":  lambda option: SEGMENTED_CONTROL_OPTIONS["duration"][option],
                "extra_callback": update_duration_box_on_change,
            },
        },
        "number_input_box": {
            "duration": {
                "label": "Duration in seconds",
                "value": int(SEGMENTED_CONTROL_OPTIONS["duration"][DEFAULT_DURATION_INDEX]),
                "disabled": lambda: st.session_state["config"]["segmented_control"]["duration"]["value"] != 3,
                "step": 1
            },
            "game_input_box": {"framework": "custom"},
        },
    }

DEFAULT_WIDGETS_V_02 = {
    "checkbox": {
        "pos_answers_only": {
            "label": "positive answers only?",
            "extra_callback": update_disabled_boxes_on_change(type_="subtract_ints", disabled_box="c")
        },
        "fade_problem": {
            "label": "fade problem after set number of seconds?"
        },
    },
    "segmented_control": {
        "problem_types": {
            "options": SEGMENTED_CONTROL_OPTIONS["problem_types"],
            "value": [0,1,2,3],
            "format_func": lambda option: SEGMENTED_CONTROL_OPTIONS["problem_types"][option],
            "selection_mode": "multi"
        },
        "duration": {
            "options": SEGMENTED_CONTROL_OPTIONS["duration"],
            "value": DEFAULT_DURATION_INDEX,
            "format_func":  lambda option: SEGMENTED_CONTROL_OPTIONS["duration"][option],
            "extra_callback": update_duration_box_on_change,
        },
    },
    "number_input_box": {
        "duration": {
            "label": "Duration in seconds",
            "value": int(SEGMENTED_CONTROL_OPTIONS["duration"][DEFAULT_DURATION_INDEX]),
            "disabled": lambda: st.session_state["config"]["segmented_control"]["duration"]["value"] != 3,
            "step": 1
        },
        "game_input_box": {"framework": "custom"},
    },
}

initial_range = {
            "add_ints": ((3, 100), (3, 100)),
            "subtract_ints": ((3, 100), (3, 100)),
            "mult_ints": ((3, 12), (3, 12)),
            "div_ints": ((3, 12), (3, 12)),
        }


for type_, active_ranges_ in initial_range.items():

    operation = type_[:-5]
    disabled_ranges = Question.calc_theoretical_range(operation, active_ranges_, False)

    if type_ != "div_ints":
        disabled_box = "c"
        ranges_ = (active_ranges_[0], active_ranges_[1], disabled_ranges)
    else:
        disabled_box = "a"
        ranges_ = (disabled_ranges, active_ranges_[0], active_ranges_[1])


    for box, range_ in zip(("a", "b", "c"), ranges_):
        for suffix, val in zip(("min", "max"), range_):
            DEFAULT_WIDGETS_V_02["number_input_box"][f"{type_}_{box}_{suffix}"] = {
                "step": 1,
                "label_visibility": "collapsed",
                "value": val,
                "disabled": box == disabled_box,
                "extra_callback": update_disabled_boxes_on_change(type_, disabled_box) if box != disabled_box else None
            }





