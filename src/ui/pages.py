import streamlit as st
from PIL.ImageQt import align8to32

from src.state_management import start_game, end_game
from src.problem_generation import validate_answer, new_problem
from src.ui.widgets import LeftRightSliders, Checkbox, custom_input_box

checkbox_keys = ["add_ints_checkbox", "subtract_ints_checkbox", "mult_ints_checkbox",
                 "div_ints_checkbox"]
default_style = "text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center; min-height: 80px;"

def setup_page_ui():
    st.title("Mental Maths Application")
    st.markdown("Choose problem types and ranges")

    display_checkboxes()

    update_active_problem_types()

    display_sliders()

    no_problem_types_selected = not st.session_state["active_problem_types"]
    duration_not_set = st.session_state["duration"] <= 0

    disable_button_condition = no_problem_types_selected or duration_not_set

    if st.button("start_game", disabled=disable_button_condition):
        start_game()
        st.rerun()

def game_page_ui():
    st.title("Running game")
    st.write(f"Score: {st.session_state["game_score"]}")

    problem_details = [st.session_state['current_problem'].Problem.left,
                       st.session_state['current_problem'].Problem.operator,
                       st.session_state['current_problem'].Problem.right]

    # render 5 display columns as follows:
    # [left]   [operator]   [right]   [  =  ]   [   ? ? ?   ]
    # for example:
    # [ 5  ]   [    +   ]   [  4  ]   [  =  ]   [   ? ? ?   ]
    # then return the fifth box so we can put the custom input box inside it

    answer_column = display_problem(problem_details)

    # now modify user input box column
    with answer_column:
        user_input = custom_input_box("constant_input_key")


    if validate_answer(user_input):
        st.session_state["game_score"] += 1
        new_problem()

    # End game button
    if st.button("End", on_click=end_game):
        st.session_state.page = "setup"
        st.rerun()

def display_problem(problem_details:list, style=default_style):
    """display the problem for the user, and return the column we'll put the user input box in"""
    game_screen_columns = st.columns([1,1,1,1,2], gap="small")
    problem_details += "="

    for col, entry in enumerate(problem_details):
        with game_screen_columns[col]:
            st.markdown(
                f"<div style='{style}'>{entry}</div>",
                unsafe_allow_html=True)

    return game_screen_columns[4]

def display_checkboxes():
    """create checkbox wrappers and render them. The wrapper updates their state, i.e., ticked/not ticked."""
    problem_type_columns = st.columns(3)

    with problem_type_columns[0]:
        add_ints_checkbox = Checkbox("add_ints")
        subtract_ints_checkbox = Checkbox("subtract_ints")
        add_ints_checkbox.render_checkbox()
        subtract_ints_checkbox.render_checkbox()
    with problem_type_columns[1]:
        mult_ints_checkbox = Checkbox("mult_ints")
        div_ints_checkbox = Checkbox("div_ints")
        mult_ints_checkbox.render_checkbox()
        div_ints_checkbox.render_checkbox()
    with problem_type_columns[2]:
        duration = st.number_input("Duration in seconds", step=1, value=st.session_state["duration"])
        if st.session_state["duration"] != duration:
            print("updating internal duration value.")
            st.session_state["duration"] = duration
            st.rerun()

def update_active_problem_types():
    """example: if the integer addition and integers division checkboxes are ticked, then we update the session state:
    st.session_state["active_problem_types"] = (("add", "ints""), ("div", "ints"))"""

    st.session_state["active_problem_types"] = [
        (op_, dtype_)
        for full_key in checkbox_keys
        if st.session_state[full_key]
        for op_, dtype_, _ in [full_key.split("_")]
    ]

def display_sliders():
    """create slider wrappers and render. The wrapper updates their state, i.e., the range"""
    add_ints_sliders = LeftRightSliders("add_ints")
    subtract_ints_sliders = LeftRightSliders("subtract_ints")
    mult_ints_sliders = LeftRightSliders("mult_ints")
    div_ints_sliders = LeftRightSliders("div_ints")

    if st.session_state["add_ints_checkbox"]:
        add_ints_sliders.render()
    if st.session_state["subtract_ints_checkbox"]:
        subtract_ints_sliders.render()
    if st.session_state["mult_ints_checkbox"]:
        mult_ints_sliders.render()
    if st.session_state["div_ints_checkbox"]:
        div_ints_sliders.render()
