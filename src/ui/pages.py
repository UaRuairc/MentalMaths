import streamlit as st
from src.config.config_management import ConfigManager as cm
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
        "modifier_settings": st.container(key="modifier_settings"),
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

    game = st.session_state["Game"]
    problem_details = [
        game.Question.Problem.left,
        game.Question.Problem.op_symbol,
        game.Question.Problem.right
    ]
    user_response = render_exercise(
        problem_details=problem_details,
        should_fade=cm.get_widget_value(widget_name="fade_problem", widget_category="checkboxes"),
        problem_id=game.problem_id
        )

    game.validate_answer(user_response)

    if cm.get_widget_value(widget_name="fade_problem", widget_category="checkboxes"):
        if st.button("Show problem again"):
            st.session_state["fade_class_identifier"] += 1
            st.rerun()

    if st.button("End"):
        game.last_event = "user_pressed_end_game"


def stats_screen_ui():
    st.markdown("Nothing to show here")
