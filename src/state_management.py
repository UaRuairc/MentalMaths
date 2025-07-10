import streamlit as st
import time
from src.problem_generation import new_problem
from src.utils import debug_fragment_info

def start_game():
    print("Starting the game.")
    new_problem()
    st.session_state["is_first_problem"] = True
    st.session_state["is_game_running"] = True
    st.session_state["game_score"] = 0
    st.session_state["game_end_time"] = time.time() + st.session_state["duration"]
    st.rerun()

def end_game():
    """end game: currently sends user to setup page (later, optional results / feedback page will be added?)"""
    print("Ending the game.")
    st.session_state["is_first_problem"] = False
    st.session_state["is_game_running"] = False
    st.session_state["active_problem"] = False
    st.rerun()

def set_defaults():
    """set session state variables defaults"""
    operators = ["add", "subtract", "mult", "div"]
    widget_labels = {
        "add_ints_checkbox": "addition",
        "subtract_ints_checkbox": "subtraction",
        "mult_ints_checkbox": "multiplication",
        "div_ints_checkbox": "division",
        "pos_answers_only_checkbox": "positive answers only?",
        "fade_problem_checkbox": "fade problem after set number of seconds?",
        "add_ints_slider": ("left digit range", "right digit range"),
        "subtract_ints_slider": ("left digit range", "right digit range"),
        "mult_ints_slider": ("left digit range", "right digit range"),
        "div_ints_slider": ("divisor range", "quotient range")
    }

    config = {
        "checkboxes": {
            **{
                f"{op}_ints": {
                    "label": widget_labels[f"{op}_ints_checkbox"],
                    "value": True,
                    "on_change": None,
                    "key": f"{op}_ints_checkbox"
                }
                for op in operators
            },
            "pos_answers_only": {
                "label": widget_labels["pos_answers_only_checkbox"],
                "value": True,
                "key": "pos_answers_only_checkbox",
            },
            "fade_problem": {
                "label": widget_labels["fade_problem_checkbox"],
                "value": False,
                "key": "fade_problem_checkbox"
            }
        },
        "sliders": {
            **{
                f"{op}_ints_{side}": {
                    "label": widget_labels[f"{op}_ints_slider"][0 if side == "left" else 1],
                    "min_value": 1,
                    "max_value": 200,
                    "value": (1, 5),
                    "on_change": None,
                    "key": f"{op}_ints_{side}_slider"
                }
                for op in operators
                for side in ["left", "right"]
            },
        },

    }

    default_parameters = {
        "page": "setup",
        "active_problem_types": [],
        "game_score": 0,
        "duration_key": 120,
        "duration": 120,
        "is_first_problem": True,
        "add_ints": True,
        "subtract_ints": True,
        "mult_ints": True,
        "div_ints": True,
        "game_end_time": 0,
        "is_game_running": False,
        "active_problem": False,
        **{f"{op}_ints_checkbox": True for op in operators},
        **{f"{op}_ints_{side}_slider": (1, 5) for op in operators for side in ["left", "right"]},
        "pos_answers_only_checkbox": True,
        "config": config,
        "fade_class_identifier": 0
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


