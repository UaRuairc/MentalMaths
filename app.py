import streamlit
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import uuid
import sqlite3
from Core.simulator import CoreProblem
import random
from st_keyup import st_keyup
import streamlit.components.v1 as components

from streamlit import session_state


# from Core import CoreProblem

class Sliders():

    def __init__(self, tag):
        self.cols = st.columns(3, vertical_alignment="center")
        self.tag = tag

    def render_sliders(self):
        with self.cols[0]:
            st.write(f"{self.tag} range")
        with self.cols[1]:
            st.slider("Left digit range", min_value=0, max_value=999, value=(1, 99), step=1,
                                       key=self.tag+"_range_left")
        with self.cols[2]:
            st.slider("Right digit range", min_value=0, max_value=999, value=(1, 99), step=1,
                                       key=self.tag+"_range_right")


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

    st.session_state.setdefault("active_problem_types", [])
    st.session_state.setdefault("counter", 0)
    st.session_state.setdefault("add_ints", True)
    st.session_state.setdefault("subtract_ints", True)
    st.session_state.setdefault("mult_ints", True)
    st.session_state.setdefault("div_ints", True)
    st.session_state.setdefault("add_ints_range_left", (1, 99))
    st.session_state.setdefault("add_ints_range_right", (1, 99))
    st.session_state.setdefault("subtract_ints_range_left", (1, 99))
    st.session_state.setdefault("subtract_ints_range_right", (1, 99))
    st.session_state.setdefault("mult_ints_range_left", (1, 99))
    st.session_state.setdefault("mult_ints_range_right", (1, 99))
    st.session_state.setdefault("div_ints_range_left", (1, 99))
    st.session_state.setdefault("div_ints_range_right", (1, 99))
    st.session_state.setdefault("duration", 120)

def setup_screen():

    st.title("Mental Maths Application")
    st.markdown("Problem Types")
    problem_type_columns = st.columns(3)

    with problem_type_columns[0]:
        st.checkbox("Addition", key="add_ints")
        st.checkbox("Substraction", key="subtract_ints")
    with problem_type_columns[1]:
        st.checkbox("Multiplication", key="mult_ints")
        division = st.checkbox("Division", key="div_ints")
    with problem_type_columns[2]:
        st.number_input("Duration in seconds", key="duration")


    if st.session_state["add_ints"]:
        add_ints_columns = Sliders("add_ints")
        add_ints_columns.render_sliders()

    if st.session_state["subtract_ints"]:
        add_ints_columns = Sliders("subtract_ints")
        add_ints_columns.render_sliders()

    if st.session_state["mult_ints"]:
        add_ints_columns = Sliders("mult_ints")
        add_ints_columns.render_sliders()

    if st.session_state["div_ints"]:
        add_ints_columns = Sliders("div_ints")
        add_ints_columns.render_sliders()

    st.session_state["active_problem_types"] = [k for k in ["add_ints", "subtract_ints", "mult_ints", "div_ints"] if st.session_state[k] == True]


    start_game_button = st.button("Start", on_click=start_game, disabled= False if (st.session_state["active_problem_types"] and st.session_state["duration"] > 0) else True, key="start_game")

    if start_game_button:
        st.session_state.page = "game"

def game_screen():


    if not st.session_state["active_problem_types"]:
        st.session_state["page"] = "setup"

    # format order starts
    st.title("Running game")
    #current_type = "add_ints"
    #left_range = st.session_state[current_type + "_range_left"]
    #right_range = st.session_state[current_type + "_range_right"]
    #current_problem = CoreProblem(r_integers=[left_range, right_range], type=current_type)
    game_screen_columns = st.columns(3)

    if st.button("End", on_click=end_game):
        st.session_state.page = "setup"
        st.rerun()
    # format order ends


    # one-time state
    st.session_state.setdefault("counter", 0)

    with game_screen_columns[0]:
        empty_placeholder = st.container(height=200, border = False)
        with empty_placeholder:
            st.write("Input Answer")
            user_answer_key = f"user_answer_{st.session_state.counter}"

            user_answer = st_keyup(label="Answer", label_visibility="collapsed", key=user_answer_key)

            if user_answer and user_answer.strip().isdigit():
                if int(user_answer) == 32:
                    st.session_state.counter += 1
                    st.rerun()

def start_game():

    st.session_state.page = "game"

def end_game():

    st.session_state.page = "setup"






initialise()

if "page" not in session_state:
    st.session_state.page = "setup"

{
    "setup": setup_screen,
    "game": game_screen
}[st.session_state.page]()














