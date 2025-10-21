import streamlit as st
from src.ui.widgets import custom_input_box
from src.utils import get_fade_html, inject_fade_css
from src.config.config_management import ConfigManager as cm

default_style = ("text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; "
                 "display: flex; align-items: center; justify-content: center; min-height: 80px;")

def render_exercise(style=default_style):
    """display the problem for the user, and return the column we'll put the user input box in"""

    if st.session_state["Game"].Question.q_type is not "standard":
        raise NotImplementedError("Only standard question types are supported in the game UI at this time.")

    components, symbol, answer, question_id = st.session_state["Game"].Question.render_details()

    unique_class = f"fade-problem-{st.session_state["fade_class_identifier"]}"
    if cm.get_widget_value(widget_name="fade_problem", widget_category="checkbox"):
        html = get_fade_html(unique_class=unique_class, base_style=style)
        inject_fade_css(unique_class=unique_class)
    else:
        html = f"<div style='{style}'>"

    game_screen_columns = st.columns([1, 1, 1, 1, 2], gap="small")

    display_columns = game_screen_columns[:3]
    input_column = game_screen_columns[4]

    display_details = [components.left, symbol, components.right, "="]
    for col, detail in zip(display_columns, display_details):
        with col:
            st.markdown(f"{html} {detail}</div>",unsafe_allow_html=True)

    with input_column:
        user_input = custom_input_box(problem_id_=question_id, correct_answer=answer, key_="constant_input_key")

    return user_input