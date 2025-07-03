import os
import random
import time
import uuid
import logging
import sqlite3
import json
import streamlit as st

from Core.simulator import CoreProblem
import streamlit.components.v1 as components

from game.game_helpers import game_countdown_timer
from widgets import Slider, Checkbox, LeftRightSliders

custom_input = components.declare_component(
    "fast_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)
# region ▶ [NOT CURRENTLY USED] Currently unused db managment helpers
def create_db():
    conn = sqlite3.connect("sessions.sqlite")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_data (
        session_id TEXT,
        session_state_data TEXT,
        PRIMARY KEY (session_id)
    )
    """)
    conn.commit()
    conn.close()

def load_from_database(session_id):
    conn = sqlite3.connect("sessions.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM session_data WHERE session_id = ?", (session_id,))
    data = cursor.fetchone()
    conn.close()

    return data

def initialise():
    create_db()
    query_params = st.query_params
    session_id = query_params.get("session_id")
    if not session_id:
        st.session_state["session_id"] = str(uuid.uuid4())
    else:
        data = load_from_database(session_id)
    print("initialised..")
# endregion

# region ▶ Some logging utility.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    filename="debug.log",   # name of your log file
    filemode="a"            # append mode
)

def log_game_state(label: str):
    snapshot = {}
    for key, value in st.session_state.items():
        try:
            json.dumps(value)
            snapshot[key] = value
        except TypeError:
            # some objects not serialisable..
            snapshot[key] = repr(value)

    logging.info(f"{label}: {json.dumps(snapshot)}")
# endregion

# region ▶ Session-state defaults
operators = ["add", "subtract", "mult", "div"]
OPERATOR_API_ALIASES = {
    "add": "add",
    "subtract": "sub",
    "mult": "mult",
    "div": "div"
}
default_parameters = {
    "page": "setup",
    "active_problem_types": [],
    "game_score": 0,
    "duration": 120,
    "is_first_problem": True,
    "add_ints": True,
    "subtract_ints": True,
    "mult_ints": True,
    "div_ints": True,
    "game_end_time": 0,
    "is_game_running": False
}

for parameter, default in default_parameters.items():
    st.session_state.setdefault(parameter, default)
for op in operators:

    st.session_state.setdefault(f"{op}_ints_checkbox_config", {
        "label": f"{op}_ints",
        "value": True,
        "on_change": None,
        "key": f"{op}_ints_checkbox"
    })

    st.session_state.setdefault(f"{op}_ints_left_slider", (1,5))

    st.session_state.setdefault(f"{op}_ints_left_slider_config", {
        "label": "Left digit range",
        "min_value": 1,
        "max_value": 200,
        "step": 1,
        "value": (1, 5),
        "key": f"{op}_ints_left_slider",
        "on_change": None
    })

    st.session_state.setdefault(f"{op}_ints_right_slider",(1,5))

    st.session_state.setdefault(f"{op}_ints_right_slider_config", {
        "label": "Right digit range",
        "min_value": 1,
        "max_value": 200,
        "value": (1, 5),
        "step": 1,
        "key": f"{op}_ints_right_slider",
        "on_change": None
    })

    checkbox_keys = ["add_ints_checkbox", "subtract_ints_checkbox", "mult_ints_checkbox",
                                                 "div_ints_checkbox"]
# endregion

# region ▶ Problem generation and game logic
def new_problem(problem_type_, data_type_):
    print("Generating a new problem...")
    next_problem_op_, next_data_type_ = random.choice(st.session_state["active_problem_types"])
    next_problem_tag = next_problem_op_ + "_" + next_data_type_
    next_problem_op_ = OPERATOR_API_ALIASES[next_problem_op_]
    next_problem_range_ = LeftRightSliders(next_problem_tag).range()
    st.session_state["current_problem"] = CoreProblem(range_=next_problem_range_, problem_type_=next_problem_op_, dtype_=next_data_type_)
    st.session_state["current_problem"].calc()
    st.session_state["is_first_problem"] = False
    st.rerun()

def custom_input_box():
    result = custom_input(
        key="constant_custom_input_key",
        correctAnswer=str(st.session_state["current_problem"].answer), # correctAnswer is used by CustomInput.tsx to determine if the input field needs resetting.
        height=80,
        width=200,
    )
    if result is None:
        return ""
    return result

def validate_answer(result):
    if result and int(result) == st.session_state["current_problem"].answer:
        return True
    else:
        return False

def guard():
    # A guard function that should never be needed. But logging if it ever is needed for future debugging
    if not st.session_state["active_problem_types"]:
        log_game_state("guard() was triggered")
        st.session_state["page"] = "setup"
        return

def start_game():
    print("Starting the game.")
    st.session_state["is_first_problem"] = True
    st.session_state["game_score"] = 0
    st.session_state.page = "game"
    st.rerun()

def end_game():
    st.session_state.page = "setup"
# endregion

# region ▶ User interface


def render_game_ui():
    st.title("Running game")
    st.write(st.session_state["game_score"])
    game_screen_columns = st.columns(5)
    with game_screen_columns[0]:
        st.markdown(f"### {st.session_state['current_problem'].Problem.left}")
    with game_screen_columns[1]:
        st.markdown(f"### {st.session_state['current_problem'].Problem.operator}")
    with game_screen_columns[2]:
        st.markdown(f"### {st.session_state['current_problem'].Problem.right}")
    with game_screen_columns[3]:
        st.markdown("### =")
    with game_screen_columns[4]:
        user_input = custom_input_box()
        if validate_answer(user_input):
            st.session_state["game_score"] += 1
            new_problem("add", "ints")

    # End button
    if st.button("End", on_click=end_game):
        st.session_state.page = "setup"
        st.rerun()

def render_setup_ui():
    st.title("Mental Maths Application")
    st.markdown("Problem Types")
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
        duration = st.number_input("Duration in seconds", value=st.session_state["duration"])
        if st.session_state["duration"] != duration:
            print("updating internal duration value.")
            st.session_state["duration"] = duration

    st.session_state["active_problem_types"] = [
        (op_, dtype_)
        for full_key in checkbox_keys
        if st.session_state[full_key]
        for op_, dtype_, _ in [full_key.split("_")]
    ]

    #add_ints_sliders = Sliders("add_ints")
    #subtract_ints_sliders = Sliders("subtract_ints")
    #mult_ints_sliders = Sliders("mult_ints")
    #div_ints_sliders = Sliders("div_ints")

    slider_columns = st.columns(3)

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




    print(st.session_state["active_problem_types"])

    if st.button(
            "Start",
            disabled=not (st.session_state["active_problem_types"]
                          and st.session_state["duration"] > 0),
            key="start_game"):
        start_game()
        st.rerun()
        st.stop()


def setup_screen():

    render_setup_ui()

def game_screen():
    guard()
    if st.session_state["is_first_problem"]:
        st.session_state["game_end_time"] = time.time() + st.session_state["duration"]
        print("Making a new problem...")
        st.session_state["is_game_running"] = True
        st.session_state["is_first_problem"] = False
        new_problem("add", "ints")
        st.rerun()

    render_game_ui()
# endregion

# keep count down timer running
game_countdown_timer()

# start on the setup page
if "page" not in st.session_state:
    st.session_state.page = "setup"
{
# associated the functions needed to switch pages with the respective page names
    "setup": setup_screen,
    "game": game_screen
}[st.session_state.page]()






