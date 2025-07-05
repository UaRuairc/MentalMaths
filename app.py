import streamlit as st
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from src.problem_generation import generate_first_problem
from src.utils import guard
from src.state_management import set_defaults, game_countdown_timer
from src.utils import track_reruns
from streamlit.runtime.fragment import MemoryFragmentStorage

from src.ui.pages import game_page_ui, setup_page_ui

track_reruns("app.py start")
set_defaults()

def setup_screen():
    print("entered setup_screen")
    setup_page_ui()

def game_screen():
    print("game screen rerun")
    guard()
    if st.session_state["is_first_problem"]:
        generate_first_problem()
    game_page_ui()


game_countdown_timer()

# start on the setup page
if "page" not in st.session_state:
    st.session_state.page = "setup"
{
# associated the functions needed to switch pages with the respective page names
    "setup": setup_screen,
    "game": game_screen
}[st.session_state.page]()






