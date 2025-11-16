import streamlit as st


def update_duration_box_on_change():
    choice_ = st.session_state["config"]["segmented_control"]["duration"]["value"]
    if choice_ is not None and choice_ != 3:
        st.session_state["config"]["number_input_box"]["duration"]["value"] = 30 * (2 ** choice_)

    if choice_ is None:
        st.session_state["config"]["number_input_box"]["duration"]["value"] = None

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
    from src.ui.widgets.widgets import custom_input_box
    WIDGET_CALLABLES["custom"]["number_input_box"] = custom_input_box

DEFAULT_WIDGETS = {

        "checkbox": {
            "add_ints": {"label": "addition"},
            "subtract_ints": {"label": "subtraction"},
            "mult_ints": {"label": "multiplication"},
            "div_ints": {"label": "division"},
            "pos_answers_only": {"label": "positive answers only?"},
            "fade_problem": {"label": "fade problem after set number of seconds?"},
        },
        #"slider": {
            #"add_ints_left": "left digit range",
            #"subtract_ints_left": "left digit range",
            #"mult_ints_left": "left digit range",
            #"div_ints_left": "divisor range",
            #"add_ints_right": "right digit range",
            #"subtract_ints_right": "right digit range",
            #"mult_ints_right": "right digit range",
            #"div_ints_right": "quotient range"
        #},

        "segmented_control": {
            "problem_types": {
                "options": SEGMENTED_CONTROL_OPTIONS["problem_types"],
                "value": [0],
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

        "slider": {
            **{f"{op}_ints_{side}":
                {
                    "label": f"{side} digit range",
                    "min_value": 1,
                    "max_value": 200,
                    "value": (1, 9),
                }
               for op in OPERATORS for side in ["left", "right"]},
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


