import streamlit as st
from src.ui.widgets import custom_input_box
from src.utils import get_fade_html, inject_fade_css

default_style = ("text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; "
                 "display: flex; align-items: center; justify-content: center; min-height: 80px;")

def render_exercise(problem_details: tuple, problem_id, style=default_style, should_fade=True):
    """display the problem for the user, and return the column we'll put the user input box in"""
    unique_class = f"fade-problem-{st.session_state["fade_class_identifier"]}"
    if should_fade:
        html = get_fade_html(unique_class=unique_class, base_style=style)
        inject_fade_css(unique_class=unique_class)
    else:
        html = f"<div style='{style}'>"

    left, op_symbol, right, ans = problem_details
    game_screen_columns = st.columns([1, 1, 1, 1, 2], gap="small")

    display_columns = game_screen_columns[:3]
    input_column = game_screen_columns[4]

    display_details = [left, op_symbol, right, "="]
    for col, detail in zip(display_columns, display_details):
        with col:
            st.markdown(f"{html} {detail}</div>",unsafe_allow_html=True)

    with input_column:
        user_input = custom_input_box(problem_id_=problem_id, correct_answer=ans, key_="constant_input_key")

    return user_input