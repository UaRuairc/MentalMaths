import streamlit as st
from src.ui.widgets import custom_input_box
from src.utils import get_fade_html, inject_fade_css

default_style = ("text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; "
                 "display: flex; align-items: center; justify-content: center; min-height: 80px;")

def render_exercise(problem_details: list, style=default_style, should_fade=True, problem_id=0):
    """display the problem for the user, and return the column we'll put the user input box in"""
    unique_class = f"fade-problem-{st.session_state["fade_class_identifier"]}"

    if should_fade:
        html = get_fade_html(unique_class=unique_class, base_style=style)
        inject_fade_css(unique_class=unique_class)
    else:
        html = f"<div style='{style}'>"

    game_screen_columns = st.columns([1, 1, 1, 1, 2], gap="small")
    problem_details_columns = game_screen_columns[:4]
    input_box_column = game_screen_columns[4]

    problem_details += "="


    for col, entry in zip(problem_details_columns, problem_details):
        with col:
            st.markdown(f"{html} {entry}</div>",unsafe_allow_html=True)

    with input_box_column:
        user_input = custom_input_box(key_="constant_input_key", problem_id_=problem_id)

    return user_input