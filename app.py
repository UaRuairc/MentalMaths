import streamlit as st
from src.state_management import set_defaults
from page_navigation import initialise_and_begin_navigation
from src.database.db_management import init_connection

#track_reruns("app.py start")

if "supabase_client" not in st.session_state:
    with st.spinner("Initializing supabase client"):
        st.session_state["supabase_client"] = init_connection()
    # this rerun prevents a visual bug on setup. to do: figure out why
    st.rerun()

set_defaults()

if st.session_state["is_game_running"]:
    st.set_page_config(initial_sidebar_state="collapsed")
    exec(open("pages/game_screen.py").read())

else:
    st.set_page_config(initial_sidebar_state="expanded")
    initialise_and_begin_navigation()