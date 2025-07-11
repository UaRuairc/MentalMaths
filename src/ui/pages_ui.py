import streamlit as st
from google.protobuf.internal import containers

from src.state_management import start_game, end_game
from src.problem_generation import validate_answer, new_problem
from src.ui.widgets import LeftRightSliders, Checkbox, custom_input_box
from src.ui.widgets import LeftRightSliders, Checkbox, custom_input_box, InputBox
import warnings
warnings.filterwarnings("ignore", message=".*was created with a default value.*")

checkbox_keys = ["add_ints_checkbox", "subtract_ints_checkbox", "mult_ints_checkbox",
                 "div_ints_checkbox"]
default_style = "text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center; min-height: 80px;"



def setup_page_ui():
    st.title("Mental Maths Application")
    settings_containers = {
        "base_settings": st.container(key="base_settings"),
        "sliders": st.container(key="sliders"),
        "extra_settings": st.container(key="extra_settings")
    }
    display_settings(settings_containers)

    no_types_selected = not st.session_state["active_problem_types"]
    duration_not_set = st.session_state["duration"] <= 0
    disable_start_button_condition = no_types_selected or duration_not_set

    help_message = (
    "Please select at least one problem type and set a duration to begin the game" if no_types_selected and duration_not_set else
    "Please select at least one problem type to begin the game" if no_types_selected else
    "Please set a duration to begin the game" if duration_not_set else
    None
     )

    if st.button("start_game", disabled=disable_start_button_condition, help=help_message):
        start_game()

def game_page_ui():
    st.title("Running game")
    st.write(f"Score: {st.session_state["game_score"]}")
    problem_details = [
        st.session_state['current_problem'].Problem.left,
        st.session_state['current_problem'].Problem.operator,
        st.session_state['current_problem'].Problem.right
    ]

    # render 5 display columns as follows:
    # [left]   [operator]   [right]   [  =  ]   [   ? ? ?   ]
    # for example:
    # [ 5  ]   [    +   ]   [  4  ]   [  =  ]   [   ? ? ?   ]
    # then return the fifth box so we can put the custom input box inside it

    user_input = render_exercise(
        problem_details=problem_details,
        should_fade=st.session_state["config"]["checkboxes"]["fade_problem"]["value"],
        )

    if validate_answer(user_input):
        st.session_state["game_score"] += 1
        new_problem()
        st.rerun()

    if st.session_state["config"]["checkboxes"]["fade_problem"]["value"]:
        if st.button("Show problem again"):
            st.session_state["fade_class_identifier"] += 1
            st.rerun()

    if st.button("End"):
        end_game()

def inject_fade_css(unique_class):
    st.markdown(f"""
            <style>
            @keyframes fadeAnimation{st.session_state["fade_class_identifier"]} {{
                from {{ opacity: 1; }}
                to {{ opacity: 0; }}
            }}
            .{unique_class} {{
                animation: fadeAnimation{st.session_state["fade_class_identifier"]} 1s ease-in-out forwards;
                animation-delay: 1s;
            }}
            </style>
            """, unsafe_allow_html=True)

def get_fade_html(unique_class, base_style=default_style):
    return f"<div class='{unique_class}' style='{base_style}'>"

def render_exercise(problem_details: list, style=default_style, should_fade=True):
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
        user_input = custom_input_box("constant_input_key")

    return user_input

def base_settings(settings_containers):
    with settings_containers["base_settings"]:
        st.markdown("Choose base settings")

        base_settings_cols = st.columns(3)

        base_ui_positioning = {
            "checkboxes": {
                "add_ints": base_settings_cols[0],
                "subtract_ints": base_settings_cols[0],
                "mult_ints": base_settings_cols[1],
                "div_ints": base_settings_cols[1]
            },
            "input_box": {
                "duration": base_settings_cols[2],
            }

        }
        for widget_category, widget_column_pairs in base_ui_positioning.items():

            if widget_category == "checkboxes":
                for checkbox, column in widget_column_pairs.items():
                    with column:
                        Checkbox(checkbox).render_checkbox()

            if widget_category == "input_box":
                for input_box, column in widget_column_pairs.items():
                    with column:
                        InputBox(input_box).render()


def extra_settings(settings_containers):
    """create checkbox wrappers and render them. The wrapper updates their state, i.e. ticked/not ticked."""
    with settings_containers["extra_settings"]:
        st.write("extra settings:")
        pos_answers_only_checkbox = Checkbox("pos_answers_only")
        pos_answers_only_checkbox.render_checkbox()
        fade_problem_checkbox = Checkbox("fade_problem")
        fade_problem_checkbox.render_checkbox()

def update_active_problem_types():
    """example: if the integer addition and integers division checkboxes are ticked, then we update the session state:
    st.session_state["active_problem_types"] = (("add", "ints""), ("div", "ints"))"""

    st.session_state["active_problem_types"] = [
        (op_, dtype_)
        for full_key in checkbox_keys
        if st.session_state[full_key]
        for op_, dtype_, _ in [full_key.split("_")]
    ]

def display_range_sliders(settings_containers):
    """create slider wrappers and render. The wrapper updates their state, i.e. the range"""
    with settings_containers["sliders"]:
        for op, type in st.session_state["active_problem_types"]:
            LeftRightSliders(f"{op}_{type}").render()

def display_settings(settings_containers):
    base_settings(settings_containers)
    extra_settings(settings_containers)
    update_active_problem_types()
    display_range_sliders(settings_containers)

def stats_screen_ui():
    st.markdown("Nothing to show here")

