import streamlit as st
from google.protobuf.internal import containers

from src.state_management import start_game, end_game
from src.problem_generation import validate_answer, new_problem
from src.ui.widgets import LeftRightSliders, custom_input_box, MakeWidget
from src.utils import get_fade_html, inject_fade_css

import warnings
warnings.filterwarnings("ignore", message=".*was created with a default value.*")

checkbox_keys = ["add_ints_checkbox", "subtract_ints_checkbox", "mult_ints_checkbox",
                 "div_ints_checkbox"]
problem_types = ["add_ints", "subtract_ints", "mult_ints",
                 "div_ints"]

default_style = "text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center; min-height: 80px;"

problem_type_index_map = {
    0: {"operation": "add",      "dtype": "ints"},
    1: {"operation": "subtract", "dtype": "ints"},
    2: {"operation": "mult",     "dtype": "ints"},
    3: {"operation": "div",      "dtype": "ints"},
}


def setup_page_ui(version=2):
    st.title("Mental Maths Application")

    settings_containers = {
        "base_settings": st.container(key="base_settings"),
        "sliders": st.container(key="sliders"),
        "extra_settings": st.container(key="extra_settings"),
        "start_button": st.container(key="start_button"),
    }
    display_settings(settings_containers, version)

    current_duration_value = st.session_state["config"]["number_input_boxes"]["duration"]["value"]
    current_duration_option = st.session_state["config"]["segmented_control"]["duration"]["value"]

    no_types_selected = not st.session_state["active_problem_types"]
    duration_not_set =  (
        current_duration_option is None or
        current_duration_value is None or
        current_duration_value <= 0
    )
    disable_start_button_condition = no_types_selected or duration_not_set

    help_message = (
    "Please select at least one problem type and set a duration to begin the game" if no_types_selected and duration_not_set else
    "Please select at least one problem type to begin the game" if no_types_selected else
    "Please set a duration to begin the game" if duration_not_set else
    None
     )

    with settings_containers["start_button"]:
        col1, col2 = st.columns([1,4],vertical_alignment="center")
        with col1:
            if st.button("start_game", disabled=disable_start_button_condition, help=help_message):
                start_game()
        with col2:
            if help_message:
                st.info(help_message)

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

    user_response = render_exercise(
        problem_details=problem_details,
        should_fade=st.session_state["config"]["checkboxes"]["fade_problem"]["value"],
        problem_id=st.session_state["problem_id"]
        )

    if validate_answer(user_response):
        st.session_state["game_score"] += 1
        st.session_state["problem_id"] += 1
        new_problem()
        st.rerun()

    if st.session_state["config"]["checkboxes"]["fade_problem"]["value"]:
        if st.button("Show problem again"):
            st.session_state["fade_class_identifier"] += 1
            st.rerun()

    if st.button("End"):
        end_game()

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

def base_settings_old(settings_containers):
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
            "number_input_boxes": {
                "duration": base_settings_cols[2],
            }

        }
        for widget_category, widget_column_pairs in base_ui_positioning.items():

            if widget_category == "checkboxes":
                for checkbox_config, column in widget_column_pairs.items():
                    with column:
                        MakeWidget(widget_config_key=checkbox_config, widget_category=widget_category).render()
                        #Checkbox(checkbox).render_checkbox()

            if widget_category == "number_input_boxes":
                for input_box_config, column in widget_column_pairs.items():
                    with column:
                        MakeWidget(widget_config_key=input_box_config, widget_category=widget_category).render()

def base_settings(settings_containers):
    with settings_containers["base_settings"]:

        base_settings_cols = st.columns(3, vertical_alignment="center")

        base_ui_positioning = {
            "segmented_control": {
                "problem_types": base_settings_cols[0],
                "duration": base_settings_cols[1],
            },
            "number_input_boxes": {
                "duration": base_settings_cols[2],
            }

        }

        build_ui_from_map(positioning_map=base_ui_positioning)

def extra_settings(settings_containers):
    """create checkbox wrappers and render them. The wrapper updates their state, i.e. ticked/not ticked."""
    with settings_containers["extra_settings"]:
        st.write("extra settings:")
        extra_settings_cols = st.columns(1, vertical_alignment="center")

        extra_ui_positioning = {
            "checkboxes": {
                "pos_answers_only": extra_settings_cols[0],
                "fade_problem": extra_settings_cols[0],
            }
        }

        build_ui_from_map(positioning_map=extra_ui_positioning)

def update_active_problem_types_old():
    """example: if the integer addition and integers division checkboxes are ticked, then we update the session state:
    st.session_state["active_problem_types"] = (("add", "ints""), ("div", "ints"))"""

    st.session_state["active_problem_types"] = [
        (op_, dtype_)
        for full_key in checkbox_keys
        if st.session_state[full_key]
        for op_, dtype_, _ in [full_key.split("_")]
    ]

def update_active_problem_types():
    """example: if the integer addition and integers division checkboxes are ticked, then we update the session state:
    st.session_state["active_problem_types"] = (("add", "ints""), ("div", "ints"))"""

    st.session_state["active_problem_types"] = [
        (problem_type_index_map[index_]["operation"], problem_type_index_map[index_]["dtype"])
        for index_ in sorted(st.session_state["config"]["segmented_control"]["problem_types"]["value"])
    ]
    print(st.session_state["config"]["segmented_control"]["problem_types"]["value"])
    print(st.session_state["active_problem_types"])

def display_range_sliders(settings_containers):
    """create slider wrappers and render. The wrapper updates their state, i.e. the range"""
    with settings_containers["sliders"]:
        for op, type in st.session_state["active_problem_types"]:
            LeftRightSliders(f"{op}_{type}").render()

def display_settings(settings_containers, version=2):
    if version == 2:
        base_settings(settings_containers)
        extra_settings(settings_containers)
        update_active_problem_types()
        display_range_sliders(settings_containers)
    else:
        base_settings_old(settings_containers)
        extra_settings(settings_containers)
        update_active_problem_types_old()
        display_range_sliders(settings_containers)

def build_ui_from_map(positioning_map):
    for widget_category, widget_column_pairs in positioning_map.items():
        for widget_config, column in widget_column_pairs.items():
            with column:
                MakeWidget(widget_config_key=widget_config, widget_category=widget_category).render()

def stats_screen_ui():
    st.markdown("Nothing to show here")

