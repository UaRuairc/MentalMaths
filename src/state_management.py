import streamlit as st
import time
from src.problem_generation import new_problem
from src.ui.widgets import custom_input_box
from src.utils import debug_fragment_info

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
    operators = ["add", "subtract", "mult", "div"]
    widget_labels = {
        "checkboxes":{
            "add_ints": "addition",
            "subtract_ints": "subtraction",
            "mult_ints": "multiplication",
            "div_ints": "division",
            "pos_answers_only": "positive answers only?",
            "fade_problem": "fade problem after set number of seconds?",
        },
        "sliders":{
            "add_ints": ("left digit range", "right digit range"),
            "subtract_ints": ("left digit range", "right digit range"),
            "mult_ints": ("left digit range", "right digit range"),
            "div_ints": ("divisor range", "quotient range"),
        },
        "number_input_boxes":{
            "duration": "Duration in seconds",
        },
        "custom_input_boxes":{
            "custom_input": None
        }

        
        
        
        
        
    }
    segmented_control_options = {
        "problem_types": {
            0: r"$+$",
            1: r"$-$",
            2: r"$\times$",
            3: r"$\div$"
        },
        "duration" : {
                0: r"30",
                1: r"60",
                2: r"120",
                3: r"..."
            }
    }

    # make a new .py file if we get too many of these
    def update_duration_box_on_change():
        choice_ = st.session_state["config"]["segmented_control"]["duration"]["value"]
        if choice_ is not None and choice_ != 3:
            st.session_state["config"]["number_input_boxes"]["duration"]["value"] = 30 * (2 ** choice_)

        if choice_ is None:
            st.session_state["config"]["number_input_boxes"]["duration"]["value"] = None

    config = {
        "checkboxes": {
            **{
                f"{op}_ints": {
                    "label": widget_labels["checkboxes"][f"{op}_ints"],
                    "value": True,
                    "on_change": None,
                    "key": f"{op}_ints_checkbox",
                    "widget_category": "checkboxes"
                }
                for op in operators
            },
            "pos_answers_only": {
                "label": widget_labels["checkboxes"]["pos_answers_only"],
                "value": True,
                "on_change": None,
                "key": "pos_answers_only_checkbox",
                "widget_category": "checkboxes"
            },
            "fade_problem": {
                "label": widget_labels["checkboxes"]["fade_problem"],
                "value": False,
                "on_change": None,
                "key": "fade_problem_checkbox",
                "widget_category": "checkboxes"
            }
        },
        "sliders": {
            **{
                f"{op}_ints_{side}": {
                    "label": widget_labels["sliders"][f"{op}_ints"][0 if side == "left" else 1],
                    "min_value": 1,
                    "max_value": 200,
                    "value": (1, 9),
                    "on_change": None,
                    "key": f"{op}_ints_{side}_slider",
                    "widget_category": "sliders"
                }
                for op in operators
                for side in ["left", "right"]
            },
        },

        "number_input_boxes": {
            "duration": {
                "label": widget_labels["number_input_boxes"]["duration"],
                "label_visibility": "hidden",
                "step": 1,
                "value": 120,
                "key": "duration_box",
                "widget_category": "number_input_boxes",
                "icon": ":material/pace:",
                "disabled": lambda: st.session_state["config"]["segmented_control"]["duration"]["value"] != 3
            },
        },
        "custom_input_boxes": {
            "user_input":{
                "key": "constant_input_key",
                "alignment_": "center",
                "value": None,
                "correctAnswer": None,
                "widget_category": "custom_input_boxes"
            }
        },
        "segmented_control": {
            "problem_types":{
                "label": "problem types",
                "options": segmented_control_options["problem_types"],
                "format_func": lambda option: segmented_control_options["problem_types"][option],
                "selection_mode": "multi",
                "label_visibility": "hidden",
                "key": "problem_selection",
                "widget_category": "segmented_control",
                "value": [0],
            },
            "duration": {
                "label": "duration",
                "options": segmented_control_options["duration"],
                "format_func": lambda option: segmented_control_options["duration"][option],
                "selection_mode": "single",
                "label_visibility": "hidden",
                "key": "duration_selection",
                "widget_category": "segmented_control",
                "value": 2,
                "extra_callback": lambda: update_duration_box_on_change(),
            }
        }
    }

    default_parameters = {
        "active_problem_types": [],
        "game_score": 0,
        "game_end_time": 0,
        "is_game_running": False,
        "config": config,
        "fade_class_identifier": 0,
        "game_mode_selection": None,
        "problem_id": 0,
        "callables": {
            "checkboxes": st.checkbox,
            "sliders": st.slider,
            "number_input_boxes": st.number_input,
            "custom_input_boxes": custom_input_box,
            "segmented_control": st.segmented_control
            },
        "problem_selection": [0]
        }

    for parameter, default in default_parameters.items():
        st.session_state.setdefault(parameter, default)

    return

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


