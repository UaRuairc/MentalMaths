import streamlit as st
import time
import inspect
from src.database.connection import init_connection
from src.problem_generation import new_problem
from src.ui.widgets import custom_input_box, MakeWidget
from src.utils import debug_fragment_info
from src.utils import file_log

from collections import defaultdict

def start_game():
    print("Starting the game.")
    new_problem()
    st.session_state["is_game_running"] = True
    st.session_state["game_score"] = 0
    st.session_state["game_end_time"] = time.time() + st.session_state["config"]["number_input_boxes"]["duration"]["value"]
    st.rerun()

def end_game():
    """end game: currently sends user to setup page (later, optional results / feedback page will be added?)"""
    print("Ending the game.")
    st.session_state["is_game_running"] = False
    st.rerun()

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
        "symbols": {
            "add": r"$+$",
            "subtract": r"$-$",
            "mult": r"$\times$",
            "div": r"$\div$",
        },
        "callables": {
            "checkboxes": st.checkbox,
            "sliders": st.slider,
            "number_input_boxes": st.number_input,
            "custom_input_boxes": custom_input_box,
            "segmented_control": st.segmented_control,
            "text_input_boxes": st.text_input,
            "buttons": st.button,
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

class ConfigManager:

    @staticmethod
    def generate_config(name: str, widget_category: str, **overrides):
        if "callables" not in st.session_state:
            st.session_state["callables"] = {
                "checkboxes": st.checkbox,
                "sliders": st.slider,
                "number_input_boxes": st.number_input,
                "custom_input_boxes": custom_input_box,
                "segmented_control": st.segmented_control
            }

        #Generate config for any widget type using introspection
        widget_callable = st.session_state["callables"][widget_category]
        sig = inspect.signature(widget_callable)
        config = {}

        for param_name, param in sig.parameters.items():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            if param.default is not inspect.Parameter.empty:
                config[param_name] = param.default
                continue

            # doesn't have a default, needs to be set, assume user provides overrides.
            config[param_name] = None


        # This is a bit hacky, functional, but improve later...
        config["widget_category"] = widget_category
        config["name"] = name
        if widget_category[-5:] == "boxes":
            config["key"] = f"{name}_{widget_category[:-2]}"
        elif widget_category == "sliders":
            config["key"] = f"{name}_{widget_category[:-1]}"
        else:
            config["key"] = f"{name}_{widget_category}"

        config["label"] = f"{name}"
        config["on_change"] = None

        if widget_category == "number_input_boxes":
            config["value"] = 0

        # some streamlit widgets do not have a `value` parameter
        #
        # MakeWidget generically uses the value param to store info on how to rebuild the widget, whether the widget has
        # a `value` parameter or not. MakeWidget then updates the config so "value" is renamed to whatever key that widget uses
        if "value" not in config:
            config["value"] = None
        # Apply overrides
        for param in overrides:
            config[param] = overrides[param]

        return config

    @staticmethod
    def add_to_session_state(config):
        config_copy = config.copy()

        name = config["name"]
        config_copy.pop("name")

        category = config["widget_category"]
        st.session_state["config"][category][name] = config_copy
        if st.session_state["suppress"] == False:
            print("\n Added config to session state: {}\n".format(st.session_state["config"][category][name] ))

    @staticmethod
    def validate_config(widget_key, widget_category):
        MakeWidget(widget_key, widget_category)
        # work in progress

    @staticmethod
    def add_widget(name: str, widget_category: str, **overrides):
        if name in st.session_state["config"][widget_category]:
            # print(f"A {widget_category} widget with this name already exists. Choose a different name.")
            return

        config = ConfigManager.generate_config(name, widget_category, **overrides)

        ConfigManager.add_to_session_state(config)


    @staticmethod
    def remove_widget(name: str, widget_category: str):
        st.session_state["config"][widget_category].pop(name)

@st.fragment(run_every=2)
def game_countdown_timer():
    #debug_fragment_info("Game Timer")

    if st.session_state["is_game_running"]:
        time_remaining = st.session_state["game_end_time"] - time.time()
        time_run_out = time_remaining <= 0
        print(f"Time remaining: {time_remaining}")

        if time_run_out :
            print("Game has ended.")
            end_game()

# make a new .py file if we get too many of these
def update_duration_box_on_change():
    choice_ = st.session_state["config"]["segmented_control"]["duration"]["value"]
    if choice_ is not None and choice_ != 3:
        st.session_state["config"]["number_input_boxes"]["duration"]["value"] = 30 * (2 ** choice_)

    if choice_ is None:
        st.session_state["config"]["number_input_boxes"]["duration"]["value"] = None
# add any overrides here for the widgets that are made on startup
def set_default_config(suppress=True):
    if "suppress" not in st.session_state:
        st.session_state["suppress"] = suppress

    if "config" in st.session_state:
        #print("default config already set.")
        return

    print("session state has no config, initialising config")
    def tree():
        return defaultdict(tree)

    config = tree()
    st.session_state["config"] = config

    operators = ["add", "subtract", "mult", "div"]
    widget_labels = {
        "checkboxes": {
            "add_ints": "addition",
            "subtract_ints": "subtraction",
            "mult_ints": "multiplication",
            "div_ints": "division",
            "pos_answers_only": "positive answers only?",
            "fade_problem": "fade problem after set number of seconds?",
        },
        "sliders": {
            "add_ints_left": "left digit range",
            "subtract_ints_left": "left digit range",
            "mult_ints_left": "left digit range",
            "div_ints_left": "divisor range",
            "add_ints_right": "right digit range",
            "subtract_ints_right": "right digit range",
            "mult_ints_right": "right digit range",
            "div_ints_right": "quotient range"
        },
        "number_input_boxes": {
            "duration": "Duration in seconds",
        },
        "custom_input_boxes": {
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
        "checkboxes": {
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
        "sliders": {
            **{f"{op}_ints_{side}":
                {
                    "label": f"{side} digit range",
                    "min_value": 1,
                    "max_value": 200,
                    "value": (1, 9),
                }
               for op in operators for side in ["left", "right"]},
            },

        "number_input_boxes": {
            "duration": {
                "label": "Duration in seconds",
                "value": int(segmented_control_options["duration"][default_duration]),
                "disabled": lambda: st.session_state["config"]["segmented_control"]["duration"]["value"] != 3,
                "step": 1
            }


        },

        }

    for widget_category, widgets in widget_labels.items():
        if widget_category == "custom_input_boxes":
            continue

        for widget_name, widget_label in widgets.items():
            overrides = (widget_overrides.get(widget_category, {}).get(widget_name, {}))

            #print(f"about to add {widget_name} : {widget_category}")
            ConfigManager.add_widget(
                name = widget_name,
                widget_category=widget_category,
                **overrides
            )
    if not st.session_state["suppress"]:
        print("Initialisation complete. To suppresses these startup messages, call set_default_config(suppress=True) in `state_management.py` instead.")