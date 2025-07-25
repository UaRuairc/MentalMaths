import streamlit as st
from src.problem_management.problem_engine import Question
from src.problem_management.problem_generation import validate_answer, new_problem
from src.config.config_management import ConfigManager
from src.state_management.game_state import start_game, end_game
from src.ui.widgets import LeftRightSliders, custom_input_box, MakeWidget
from src.utils import get_fade_html, inject_fade_css
from src.ui.auth_ui import auth_ui

import warnings
warnings.filterwarnings("ignore", message=".*was created with a default value.*")

checkbox_keys = ["add_ints_checkbox", "subtract_ints_checkbox", "mult_ints_checkbox",
                 "div_ints_checkbox"]
default_style = ("text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; "
                 "display: flex; align-items: center; justify-content: center; min-height: 80px;")
# currently dynamically make some widget configurations on this page at runtime, so defaults not in config yet, initialise here
initial_range = {
    "add_ints": [(3,100), (3,100)],
    "subtract_ints": [(3,100), (3,100)],
    "mult_ints": [(3,12), (3,12)],
    "div_ints": [(3,12), (3,12)],
}
for key, val in initial_range.items():
    # for now, key is always <operation_ints>, so `[:-5]` gets rid of the ints
    operation = key[:-5]
    ans_range = Question.calc_theoretical_range(key[:-5], val)
    if key != "div_ints":
        initial_range[key].append(ans_range)
    else:
        initial_range[key].insert(0, ans_range)

def setup_page_ui(version=2):
    with st.sidebar:
        auth_ui()

    st.title("Mental Maths Application")

    settings_containers = {
        "base_settings": st.container(key="base_settings"),
        "range_settings": st.container(key="range_settings"),
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

def display_range_row(type_, initial_range_, symbol="+"):
    digit_range = st.columns([1, 8, 1, 8, 1, 8, 1], vertical_alignment="center")
    r_ = initial_range_
    st.markdown(
            """
            <style>
            /* Center all markdown content */
            [data-testid="stMarkdown"]{
                display:flex;
                align-items:center;
                justify-content:center;
                height:100%;
                width:100%;
                margin:0;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


    left_container_disabled = (type_ == "div_ints")
    right_container_disabled = (type_ != "div_ints")

    def update_disabled_box_on_change():
        if type_ == "div_ints":
            enabled_boxes = (f"second_{type_}_operand_range_left", f"second_{type_}_operand_range_right",
                             f"answer_{type_}_range_left", f"answer_{type_}_range_right")

            disabled_boxes = (f"first_{type_}_operand_range_left", f"first_{type_}_operand_range_right")
        else:
            enabled_boxes = (f"first_{type_}_operand_range_left", f"first_{type_}_operand_range_right",
                            f"second_{type_}_operand_range_left", f"second_{type_}_operand_range_right")


            disabled_boxes = (f"answer_{type_}_range_left", f"answer_{type_}_range_right")

        l1, r1 = (st.session_state["config"]["number_input_boxes"][enabled_boxes[0]]["value"],
                  st.session_state["config"]["number_input_boxes"][enabled_boxes[1]]["value"])
        l2, r2 = (st.session_state["config"]["number_input_boxes"][enabled_boxes[2]]["value"],
                  st.session_state["config"]["number_input_boxes"][enabled_boxes[3]]["value"])

        print(st.session_state["config"]["checkboxes"]["pos_answers_only"]["value"])
        min_, max_ = Question.calc_theoretical_range(
            type_=type_[:-5],
            ranges_=([l1, r1], [l2, r2]),
            positive_answers_only=lambda: st.session_state["config"]["checkboxes"]["pos_answers_only"]["value"])

        st.session_state["config"]["number_input_boxes"][disabled_boxes[0]]["value"] = min_
        st.session_state["config"]["number_input_boxes"][disabled_boxes[1]]["value"] = max_


    ConfigManager.add_widget(f"first_{type_}_operand_range_left", "number_input_boxes",
                             **{"step": 1, "label_visibility": "collapsed", "value": r_[0][0]}, disabled=left_container_disabled,
                             extra_callback = lambda: update_disabled_box_on_change())
    ConfigManager.add_widget(f"first_{type_}_operand_range_right", "number_input_boxes",
                             **{"step": 1, "label_visibility": "collapsed", "value": r_[0][1]}, disabled=left_container_disabled,
                             extra_callback = lambda: update_disabled_box_on_change())

    ConfigManager.add_widget(f"second_{type_}_operand_range_left", "number_input_boxes",
                             **{"step": 1, "label_visibility": "collapsed", "value": r_[1][0]},
                             extra_callback = lambda: update_disabled_box_on_change())
    ConfigManager.add_widget(f"second_{type_}_operand_range_right", "number_input_boxes",
                             **{"step": 1, "label_visibility": "collapsed", "value": r_[1][1]},
                             extra_callback = lambda: update_disabled_box_on_change())

    ConfigManager.add_widget(f"answer_{type_}_range_left", "number_input_boxes",
                             **{"step": 1, "label_visibility": "collapsed", "value": r_[2][0]}, disabled=right_container_disabled,
                             extra_callback = lambda: update_disabled_box_on_change())
    ConfigManager.add_widget(f"answer_{type_}_range_right", "number_input_boxes",
                             **{"step": 1, "label_visibility": "collapsed", "value": r_[2][1]}, disabled=right_container_disabled,
                             extra_callback = lambda: update_disabled_box_on_change())



    with digit_range[1]:
        with st.container(border=True):
            placements3 = st.columns([5, 2, 5], vertical_alignment="center")
            with placements3[0]:
                MakeWidget(f"first_{type_}_operand_range_left", "number_input_boxes").render()
            with placements3[1]:
                st.markdown(":material/arrow_right_alt:")
            with placements3[2]:
                MakeWidget(f"first_{type_}_operand_range_right", "number_input_boxes").render()

    with digit_range[2]:
        st.markdown(symbol)

    with digit_range[3]:
        with st.container(border=True):
            placements2 = st.columns([5, 2, 5], vertical_alignment="center")
            with placements2[0]:
                MakeWidget(f"second_{type_}_operand_range_left", "number_input_boxes").render()
            with placements2[1]:
                st.markdown(":material/arrow_right_alt:")
            with placements2[2]:
                MakeWidget(f"second_{type_}_operand_range_right", "number_input_boxes").render()
    with digit_range[4]:
        st.markdown("=")
    with digit_range[5]:
        with st.container(border=True):
            placements2 = st.columns([5, 2, 5], vertical_alignment="center")
            with placements2[0]:
                MakeWidget(f"answer_{type_}_range_left", "number_input_boxes").render()
            with placements2[1]:
                st.markdown(":material/arrow_right_alt:")
            with placements2[2]:
                MakeWidget(f"answer_{type_}_range_right", "number_input_boxes").render()

def game_page_ui():
    st.title("Running game")
    st.write(f"Score: {st.session_state["game_score"]}")
    problem_details = [
        st.session_state['current_problem'].Problem.left,
        st.session_state['current_problem'].Problem.op,
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
                for checkbox_name, column in widget_column_pairs.items():
                    with column:
                        MakeWidget(widget_config_key=checkbox_name, widget_category=widget_category).render()
                        #Checkbox(checkbox).render_checkbox()

            if widget_category == "number_input_boxes":
                for input_box_name, column in widget_column_pairs.items():
                    with column:
                        MakeWidget(widget_config_key=input_box_name, widget_category=widget_category).render()

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
    """example: if the integer addition and integers division options are ticked, then we update the session state:
    st.session_state["active_problem_types"] = (("add", "ints""), ("div", "ints"))"""
    index_map = st.session_state["problem_type_index_map"]
    selections = sorted(st.session_state["config"]["segmented_control"]["problem_types"]["value"])
    st.session_state["active_problem_types"] = [
        (index_map[index_]["operation"], index_map[index_]["dtype"])
        for index_ in selections
    ]
    #print(st.session_state["config"]["segmented_control"]["problem_types"]["value"])
    #print(st.session_state["active_problem_types"])

def display_range_sliders(settings_containers):
    """create slider wrappers and render. The wrapper updates their state, i.e. the range"""
    with settings_containers["range_settings"]:
        for op, type in st.session_state["active_problem_types"]:
            LeftRightSliders(f"{op}_{type}").render()

def display_range_boxes(settings_containers):
    with settings_containers["range_settings"]:
        for op, type in st.session_state["active_problem_types"]:
            initial_range_ = initial_range[f"{op}_{type}"]
            display_range_row(f"{op}_{type}", initial_range_=initial_range_,  symbol=st.session_state["symbols"][op])

def display_settings(settings_containers, version=2):
    if version == 2:
        base_settings(settings_containers)
        extra_settings(settings_containers)
        update_active_problem_types()
        display_range_boxes(settings_containers)
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

