import streamlit as st
from src.problem_management.problem_generation import validate_answer, new_problem
from src.state_management.game_state import end_game
from src.ui.page_components.auth import user_auth
from src.ui.page_components.setup import display_settings, display_start_button_and_help_messages
from src.ui.page_components.game import render_exercise
import warnings
warnings.filterwarnings("ignore", message=".*was created with a default value.*")

def setup_page_ui(version=2):
    with st.sidebar:
        user_auth()

    st.title("Mental Maths Application")

    settings_containers = {
        "base_settings": st.container(key="base_settings"),
        "range_settings": st.container(key="range_settings"),
        "extra_settings": st.container(key="extra_settings"),
        "start_button": st.container(key="start_button"),
    }
    display_settings(settings_containers)

    display_start_button_and_help_messages(settings_containers)

def game_page_ui():

    """
    render 5 display columns as follows:
    [left]   [operator]   [right]   [  =  ]   [   ? ? ?   ]
    for example:
    [ 5  ]   [    +   ]   [  4  ]   [  =  ]   [   ? ? ?   ]
    then return the fifth box(the fifth column) so we can put the custom input box inside it
    """
    st.title("Running game")

    st.write(f"Score: {st.session_state["game_score"]}")

    problem_details = [
        st.session_state['current_problem'].Problem.left,
        st.session_state['current_problem'].Problem.op,
        st.session_state['current_problem'].Problem.right
    ]

    user_response = render_exercise(
        problem_details=problem_details,
        should_fade=st.session_state["config"]["checkboxes"]["fade_problem"]["value"],
        problem_id=st.session_state["problem_id"]
        )

    if validate_answer(user_response):
        st.session_state["game_score"] += 1
        st.session_state["problem_id"] += 1
        #print(f"the user response was: {user_response}")
        st.session_state["current_game_session"].update_problem_event(keystroke_sequence=user_response[2], keystroke_count=user_response[3], event="correct_answer")
        #print(st.session_state["current_game_session"].current_problem_event)
        #print(json.dumps(st.session_state["current_game_session"].current_session_event, indent=2, default=str))
        st.session_state["current_game_session"].store_problem_event()
        new_problem()
        st.rerun()

    if st.session_state["config"]["checkboxes"]["fade_problem"]["value"]:
        if st.button("Show problem again"):
            st.session_state["fade_class_identifier"] += 1
            st.rerun()

    if st.button("End"):
        end_game(event="game_ended_early")

def stats_screen_ui():
    st.markdown("Nothing to show here")
