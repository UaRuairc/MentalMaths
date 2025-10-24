import streamlit as st

from src.database.connection import init_connection
from src.config.config_management import ConfigManager
from src.ui.widgets import custom_input_box
from src.utils import file_log
from collections import defaultdict


def set_defaults():
    """set session state variables defaults"""

    default_parameters = {
        "user": None,
        "supabase_client": init_connection(),
        "expired_tokens": None,
        "supabase_tokens": None,
        "did_try_restore": False,
        "cookies_worked": False,
        "tokens_to_save": None,
        "active_problem_types": [],
        "game_score": 0,
        "game_end_time": 0,
        "is_game_running": False,
        "fade_class_identifier": 0,
        "game_mode_selection": None,
        "problem_id": 0,
        "problem_types_segmented_control": [0],
        "GameTelemetry": None,
        "symbols": {
            "add": r"$+$",
            "subtract": r"$-$",
            "mult": r"$\times$",
            "div": r"$\div$",
        },
        "callables": {
            "streamlit":{
                "checkbox": st.checkbox,
                "slider": st.slider,
                "number_input_box": st.number_input,
                "custom_input_box": custom_input_box,
                "segmented_control": st.segmented_control,
                "text_input_boxes": st.text_input,
                "buttons": st.button,
                },
            "custom": custom_input_box
        },
        "problem_type_index_map": {
            0: {"operation": "add", "dtype": "ints"},
            1: {"operation": "subtract", "dtype": "ints"},
            2: {"operation": "mult", "dtype": "ints"},
            3: {"operation": "div", "dtype": "ints"},
            },
        }

    for parameter, default in default_parameters.items():
        st.session_state.setdefault(parameter, default)

    set_default_config()

    return

def update_duration_box_on_change():
    choice_ = st.session_state["config"]["segmented_control"]["duration"]["value"]
    if choice_ is not None and choice_ != 3:
        st.session_state["config"]["number_input_box"]["duration"]["value"] = 30 * (2 ** choice_)

    if choice_ is None:
        st.session_state["config"]["number_input_box"]["duration"]["value"] = None


def set_default_config(suppress=True):
    if "suppress" not in st.session_state:
        st.session_state["suppress"] = suppress

    if "config" in st.session_state:
        #print("default config already set.")
        return

    file_log("session state has no config, initialising config")
    def tree():
        return defaultdict(tree)

    config = tree()
    st.session_state["config"] = config

    operators = ["add", "subtract", "mult", "div"]
    widget_labels = {
        "checkbox": {
            "add_ints": "addition",
            "subtract_ints": "subtraction",
            "mult_ints": "multiplication",
            "div_ints": "division",
            "pos_answers_only": "positive answers only?",
            "fade_problem": "fade problem after set number of seconds?",
        },
        "slider": {
            "add_ints_left": "left digit range",
            "subtract_ints_left": "left digit range",
            "mult_ints_left": "left digit range",
            "div_ints_left": "divisor range",
            "add_ints_right": "right digit range",
            "subtract_ints_right": "right digit range",
            "mult_ints_right": "right digit range",
            "div_ints_right": "quotient range"
        },
        "number_input_box": {
            "duration": "Duration in seconds",
        },
        "custom_input_box": {
            "custom_input": None
        },
        "segmented_control": {
            "problem_types": None,
            "duration": None
        }
    }

    segmented_control_options = {
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

    default_duration = 2

    widget_overrides = {
        "checkbox": {
            "pos_answers_only": {"label": "positive answers only?"},
            "fade_problem": {"label": "fade problem after set number of seconds?"},
        },


        "segmented_control": {
            "problem_types": {
                "options": segmented_control_options["problem_types"],
                "value": [0],
                "format_func": lambda option: segmented_control_options["problem_types"][option],
                "selection_mode": "multi"
            },
            "duration": {
                "options": segmented_control_options["duration"],
                "value": default_duration,
                "format_func":  lambda option: segmented_control_options["duration"][option],
                "extra_callback": lambda: update_duration_box_on_change(),
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
               for op in operators for side in ["left", "right"]},
            },

        "number_input_box": {
            "duration": {
                "label": "Duration in seconds",
                "value": int(segmented_control_options["duration"][default_duration]),
                "disabled": lambda: st.session_state["config"]["segmented_control"]["duration"]["value"] != 3,
                "step": 1
            }
        },
    }

    for widget_category, widgets in widget_labels.items():
        if widget_category == "custom_input_box":
            continue

        for widget_name, widget_label in widgets.items():
            overrides = (widget_overrides.get(widget_category, {}).get(widget_name, {}))

            ConfigManager.register(
                widget_name= widget_name,
                widget_category=widget_category,
                **overrides
            )
    if not st.session_state["suppress"]:
        print("Initialisation complete. To suppresses these startup messages, call set_default_config(suppress=True) in `config_management.py` instead.")