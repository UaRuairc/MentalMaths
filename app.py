import os
import uuid
import sqlite3

import streamlit as st
import pandas as pd
import numpy as np
from numpy.ma.core import left_shift

from Core.simulator import CoreProblem
import streamlit.components.v1 as components

custom_input = components.declare_component(
    "fast_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)

# region ▶ Currently unused helpers for db management
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
# endregion

# region ▶ Helpers for UI elements: wrapper + render for slider, render for checkboxes
class Sliders():

    def __init__(self, tag):
        self.cols = st.columns(3, vertical_alignment="center")
        self.tag = tag
        self.left_config = dict(st.session_state[f"{self.tag}_left_slider_config"])
        self.right_config = dict(st.session_state[f"{self.tag}_right_slider_config"])

        self.left_value = self.left_config["value"]
        self.right_value = self.right_config["value"]
        self.left_key = self.left_config["key"]
        self.right_key = self.right_config["key"]

        # self.right_config.pop("value")
        # self.left_config.pop("value")

        # initialise the values once, we do not want to keep overriding them.
        if self.left_key not in st.session_state:
            st.session_state[self.left_key] = self.left_value
        if self.right_key not in st.session_state:
            st.session_state[self.right_key] = self.right_value

        self.left_config.pop("value")
        self.right_config.pop("value")



    def render_sliders(self):
        with self.cols[0]:
            st.write(f"{self.tag} range")
        with self.cols[1]:
            val = st.slider(**self.left_config)
            if val != st.session_state[f"{self.tag}_left_slider_config"]["value"]:
                st.session_state[f"{self.tag}_left_slider_config"]["value"] = val
        with self.cols[2]:
            val = st.slider(**self.right_config)
            if val != st.session_state[f"{self.tag}_right_slider_config"]["value"]:
                st.session_state[f"{self.tag}_right_slider_config"]["value"] = val

    def range(self):
        return[st.session_state[self.left_key] , st.session_state[self.right_key]]

def draw_checkbox(problem_type_key):
    val = st.checkbox(problem_type_key, value=st.session_state[problem_type_key])
    st.session_state[problem_type_key] = val
# endregion

# region ▶ Session-state defaults
operators = ["add", "subtract", "mult", "div"]
default_parameters = {
    "active_problem_types": [],
    "counter": 0,
    "duration": 120,
    "first_problem": True,
    "fresh": True,
    "history": [],
    "add_ints": True,
    "subtract_ints": True,
    "mult_ints": True,
    "div_ints": True,
}

for parameter, default in default_parameters.items():
    st.session_state.setdefault(parameter, default)
for op in operators:
    st.session_state.setdefault(f"{op}_ints", True)

    st.session_state.setdefault(f"{op}_ints_left_slider_config", {
        "label": "Left digit range",
        "min_value": 1,
        "max_value": 999,
        "step": 1,
        "value": (1, 99),
        "key": f"{op}_left_slider"
    })
    st.session_state.setdefault(f"{op}_ints_right_slider_config", {
        "label": "Right digit range",
        "min_value": 1,
        "max_value": 999,
        "value": (1, 99),
        "step": 1,
        "key": f"{op}_right_slider"
    })
# endregion

# region ▶ Start/end game helpers
def start_game():
    print("Starting the game.")
    st.session_state["fresh"] = True
    st.session_state.page = "game"

def end_game():
    st.session_state["first_problem"] = True
    st.session_state["counter"] = 0
    st.session_state.page = "setup"
# endregion

# region ▶ helpers to generate new problems and check the answer
def make_problem(current_type):
    left_config = st.session_state[current_type + "_left_slider_config"]
    right_config = st.session_state[current_type + "_right_slider_config"]
    st.session_state["current_problem"] = CoreProblem(r_integers=Sliders("add_ints").range(), type=current_type)
    st.session_state["current_problem"].calc()
    st.session_state["first_problem"] = False
    st.rerun()

def check_answer():
    key = "constant_key"
    result = custom_input(
        key=key,
        correctAnswer=str(st.session_state["current_problem"].answer),
        height=80,
        width=200,
    )
    print(result)
    if result is None or result == "":
        return

    typed = result or ""

    st.session_state["user_answer"] = typed

    print(f"Lets check if typed result is the same as {st.session_state['current_problem'].answer}")

    # 6) On match, clear and make a new problem
    if int(typed) == st.session_state["current_problem"].answer:
        st.session_state["user_answer"] = ""
        print("making a new problem")
        make_problem("add_ints")
        # st.rerun()
# endregion

#region ▶ Unused initialisation function may use to construct db
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

# region ▶ setup and game screen, and two helpers for game display logic
def setup_screen():

    st.title("Mental Maths Application")
    st.markdown("Problem Types")

    problem_type_columns = st.columns(3)

    with problem_type_columns[0]:
        draw_checkbox("add_ints")
        draw_checkbox("subtract_ints")
    with problem_type_columns[1]:
        draw_checkbox("mult_ints")
        draw_checkbox("div_ints")
    with problem_type_columns[2]:
        duration = st.number_input("Duration in seconds", value = st.session_state["duration"])
        st.session_state["duration"] = duration

    if st.session_state["add_ints"]:
        add_ints_sliders = Sliders("add_ints")
        add_ints_sliders.render_sliders()
    if st.session_state["subtract_ints"]:
        subtract_ints_sliders = Sliders("subtract_ints")
        subtract_ints_sliders.render_sliders()
    if st.session_state["mult_ints"]:
        mult_ints_sliders = Sliders("mult_ints")
        mult_ints_sliders.render_sliders()
    if st.session_state["div_ints"]:
        div_ints_sliders = Sliders("div_ints")
        div_ints_sliders.render_sliders()

    st.session_state["active_problem_types"] = [k for k in ["add_ints", "subtract_ints", "mult_ints", "div_ints"] if st.session_state[k] == True]
    st.button("Start", on_click=start_game, disabled= False if (st.session_state["active_problem_types"] and st.session_state["duration"] > 0) else True, key="start_game")

def game_screen():

    guard()

    st.title("Running game")

    if st.session_state["first_problem"]:
        print("Making a new problem...")
        make_problem("add_ints")
        st.session_state["first_problem"] = False
        st.session_state["history"].clear()
        st.rerun()

    # format order starts
    game_display()

def game_display():
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

        check_answer()


    # End button
    if st.button("End", on_click=end_game):
        st.session_state.page = "setup"
        st.rerun()

def guard():
    if not st.session_state["active_problem_types"]:
        st.session_state["page"] = "setup"
        return
# endregion

if "page" not in st.session_state:
    st.session_state.page = "setup"
{
    "setup": setup_screen,
    "game": game_screen
}[st.session_state.page]()






