import streamlit as st
import time

@st.fragment(run_every=3)
def game_countdown_timer():
    if 0 <= int( st.session_state["game_end_time"] - time.time() ) <= 999:
        print(f"Time remaining: {int( st.session_state["game_end_time"] - time.time() )}")
    if st.session_state["is_game_running"]:
        if st.session_state["game_end_time"] - time.time() <= 0:
            print("Game has ended.")
            st.session_state["is_game_running"] = False
            st.session_state["page"] = "setup"
            st.rerun()

