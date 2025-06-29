import os
import uuid
import sqlite3

import streamlit as st
import pandas as pd
import numpy as np
from numpy.ma.core import left_shift

from Core.simulator import CoreProblem
import streamlit.components.v1 as components

fast_input = components.declare_component(
    "fast_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)

import time
# from Core import CoreProblem
variable = "test"
input_key = "my_answer"



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

operators = ["add", "subtract", "mult", "div"]
default_parameters = {
    "active_problem_types": [],
    "counter": 0,
    "duration": 120,
    "user_answer": "",
    "first_problem": True,
    "clear_ctr": 0,
    "fresh": True,
    "history": [],
    "add_ints": True,
    "subtract_ints": True,
    "mult_ints": True,
    "div_ints": True,
    "debug_counter": 0,
    "answer_value": None,
    "last_answer": None
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


if False:
    if st.session_state["debug_counter"] == 0:
        print(f"The application has been run.")


    if st.session_state["debug_counter"] != 0:
        print(f"Loop # {st.session_state["debug_counter"]}")
        print(f"The box previously contained: {st.session_state["last_answer"]}")
        print(f"The box currently contains: {st.session_state.answer_value}")

st.session_state["debug_counter"] += 1


def initialise():
    create_db()
    query_params = st.query_params
    session_id = query_params.get("session_id")
    if not session_id:
        st.session_state["session_id"] = str(uuid.uuid4())
    else:
        data = load_from_database(session_id)
    print("initialised..")

def make_problem(current_type):
    left_config = st.session_state[current_type + "_left_slider_config"]
    right_config = st.session_state[current_type + "_right_slider_config"]
    st.session_state["current_problem"] = CoreProblem(r_integers=Sliders("add_ints").range(), type=current_type)
    st.session_state["current_problem"].calc()
    st.session_state["answered"] = False
    st.session_state["fresh"] = True
    st.session_state["user_answer"] = ""
    st.session_state["clear_ctr"]+= 1
    if False:
        print(f"new problem: "
            f"{st.session_state["current_problem"].Problem.right} "
            f"{st.session_state["current_problem"].Problem.operator} "
            f"{st.session_state["current_problem"].Problem.right} "
            "= "
            f"{st.session_state["current_problem"].answer}"
        )
    st.session_state["first_problem"] = False
    st.rerun()

def check_answer():
    user_answer = st.session_state["history"].pop()
    if user_answer is None:
        #print("Not a digit (None)")
        return
    if not user_answer.isdigit():
        #print("Not a digit")
        return
    print(f"Checking {user_answer} vs actual answer {st.session_state["current_problem"].answer}")
    if int(user_answer) == int(st.session_state["current_problem"].answer):
        print("correct!")
        st.session_state["history"].clear()
        st.session_state.counter += 1
        st.session_state["answered"] = True
        st.session_state["user_answer"] = 0
        make_problem("add_ints")
        # st.rerun()

def display():
    game_screen_columns = st.columns(5)
    with game_screen_columns[0]:
        st.markdown(f"### {st.session_state["current_problem"].Problem.left}")
    with game_screen_columns[1]:
        st.markdown(f"### {st.session_state["current_problem"].Problem.operator}")
    with game_screen_columns[2]:
        st.markdown(f"### {st.session_state["current_problem"].Problem.right}")
    with game_screen_columns[3]:
        st.markdown(f"### =")
    with game_screen_columns[4]:
        empty_placeholder = st.container(height=200, border = False)
        with empty_placeholder:
            key = f"answer_input_{st.session_state["clear_ctr"]}"
            st.session_state["last_answer"] = st.session_state.answer_value
            answer = fast_input(
                height=80,
                width=200,
                key=key,
                value=st.session_state["user_answer"]
            )

            st.session_state.answer_value = answer or ""
            # print(f"The box visually contains {answer}, until you see this message the box will not visually change!")
            if answer not in st.session_state["history"] and answer is not None and not st.session_state["fresh"]:
                # print(f"we will append {answer} to history now.")
                st.session_state["history"].append(answer)
            else:
                st.session_state["fresh"] = False
                st.session_state["history"].clear()

            if st.session_state["history"]:
                print("checking...")
                check_answer()

    if st.button("End", on_click=end_game):
        st.session_state.page = "setup"
        st.rerun()

def draw_checkbox(problem_type_key):
    val = st.checkbox(problem_type_key, value=st.session_state[problem_type_key])
    st.session_state[problem_type_key] = val

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
    if not st.session_state["active_problem_types"]:
        st.session_state["page"] = "setup"
        return
    st.title("Running game")
    if input_key not in st.session_state:
        st.session_state[input_key] = ""
    if st.session_state["first_problem"]:
        make_problem("add_ints")
        st.session_state["first_problem"] = False
        st.session_state["history"].clear()

    # format order starts
    display()

def start_game():
    print("Starting the game.")
    st.session_state["fresh"] = True
    st.session_state.page = "game"

def end_game():
    st.session_state["first_problem"] = True
    st.session_state["counter"] = 0
    st.session_state.page = "setup"

# ---------------------------------------------------------------------- #

if "initialised" not in st.session_state:
    st.session_state["initialised"] = True
    initialise()

if "page" not in st.session_state:
    st.session_state.page = "setup"
{
    "setup": setup_screen,
    "game": game_screen
}[st.session_state.page]()






