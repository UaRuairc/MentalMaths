import streamlit as st
import time
from src.utils import debug_fragment_info

def start_game():
    print("Starting the game.")
    st.session_state["is_first_problem"] = True
    st.session_state["game_score"] = 0
    st.session_state.page = "game"

def end_game():
    """end game: currently sends user to setup page (later, optional results / feedback page will be added?)"""
    st.session_state["is_game_running"] = False
    st.session_state.page = "setup"

def set_defaults():
    """set session state variables defaults"""
    operators = ["add", "subtract", "mult", "div"]

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
        "is_game_running": False
    }

    for parameter, default in default_parameters.items():
        st.session_state.setdefault(parameter, default)
    for op in operators:
        st.session_state.setdefault(f"{op}_ints_checkbox_config", {
            "label": f"{op}_ints",
            "value": True,
            "on_change": None,
            "key": f"{op}_ints_checkbox"
        })

        # st.session_state.setdefault(f"{op}_ints_left_slider", (1, 5))

        st.session_state.setdefault(f"{op}_ints_left_slider_config", {
            "label": "Left digit range",
            "min_value": 1,
            "max_value": 200,
            "step": 1,
            "value": (1, 5),
            "key": f"{op}_ints_left_slider",
            "on_change": None
        })

        # st.session_state.setdefault(f"{op}_ints_right_slider", (1, 5))

        st.session_state.setdefault(f"{op}_ints_right_slider_config", {
            "label": "Right digit range",
            "min_value": 1,
            "max_value": 200,
            "value": (1, 5),
            "step": 1,
            "key": f"{op}_ints_right_slider",
            "on_change": None
        })

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

