import streamlit as st
from src.state_management import start_game, end_game
from src.problem_generation import validate_answer, new_problem
from src.ui.widgets import LeftRightSliders, Checkbox, custom_input_box

checkbox_keys = ["add_ints_checkbox", "subtract_ints_checkbox", "mult_ints_checkbox",
                 "div_ints_checkbox"]

def game_page_ui():
    st.title("Running game")
    st.write(f"Score: {st.session_state["game_score"]}")

    # display_problem creates columns and displays the users next problem in them
    # it also returns the column we'll put the user input box in
    answer_column = display_problem()

    # now modify user input box column
    with answer_column:
        user_input = custom_input_box()
        if validate_answer(user_input):
            st.session_state["game_score"] += 1
            new_problem()

    # End button
    if st.button("End", on_click=end_game):
        st.session_state.page = "setup"
        st.rerun()

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


def display_problem():
    """display the problem for the user, and return the column we'll put the user input box in"""
    game_screen_columns = st.columns(5)

    with game_screen_columns[0]:
        st.markdown(f"### {st.session_state['current_problem'].Problem.left}")
    with game_screen_columns[1]:
        st.markdown(f"### {st.session_state['current_problem'].Problem.operator}")
    with game_screen_columns[2]:
        st.markdown(f"### {st.session_state['current_problem'].Problem.right}")
    with game_screen_columns[3]:
        st.markdown("### =")

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
