import time
import streamlit as st
from src.problem_management.problem_generation import new_problem


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