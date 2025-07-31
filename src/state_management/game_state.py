import time
import uuid
import streamlit as st
from src.database.events import Session
from src.problem_management.problem_generation import new_problem
from datetime import datetime, timezone


def start_game( logged_in=False, event="game_started"):
    print("Starting the game.")
    st.session_state["game_start_time"] = time.time()
    st.session_state["game_end_time"] = st.session_state["game_start_time"] + st.session_state["config"]["number_input_boxes"]["duration"]["value"]

    if "supabase_client" in st.session_state:
        st.session_state["current_game_session"] = Session(
            session_id= str(uuid.uuid7()),
            user_id=st.session_state["supabase_client"].auth.get_user().user.id if logged_in else None,
            game_mode="standard",
            active_problem_types=st.session_state["active_problem_types"],
            started_at=datetime.now(timezone.utc),
        )
    new_problem()
    st.session_state["is_game_running"] = True
    st.session_state["game_score"] = 0
    st.rerun()


def end_game(event="game_ended_early"):
    """end game: currently sends user to setup page (later, optional results / feedback page will be added?)"""
    st.session_state["current_game_session"].update_session_event(event=event)
    print("Ending the game.")
    st.session_state["current_game_session"].store_session_event()
    st.session_state["is_game_running"] = False
    st.rerun()

@st.fragment(run_every=2)
def game_countdown_timer(verbosity=1):
    """
    Right now, we are printing debug statements. So, run_every= 2 seconds to prevent verbose output
    Will need to make a game logger helper soon
    """
    #debug_fragment_info("Game Timer")

    if st.session_state["is_game_running"]:
        time_remaining = st.session_state["game_end_time"] - time.time()
        time_run_out = time_remaining <= 0
        if verbosity == 1: print(f"Time remaining: {time_remaining}")

        if time_run_out :
            if verbosity == 1: print("Game has ended.")
            end_game(event="game_completed")