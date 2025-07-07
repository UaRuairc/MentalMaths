import streamlit as st
from src.state_management import set_defaults
from page_navigation import initialise_and_being_navigation

#track_reruns("app.py start")

set_defaults()

if st.session_state["is_game_running"]:
    exec(open("pages/game_screen.py").read())

else:
    initialise_and_being_navigation()