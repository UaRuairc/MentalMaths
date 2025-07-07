import streamlit as st
import time
import random
from src.ui.widgets import LeftRightSliders
from src.problem_engine import CoreProblem

operators = ["add", "subtract", "mult", "div"]
OPERATOR_API_ALIASES = {
    "add": "add",
    "subtract": "sub",
    "mult": "mult",
    "div": "div"
}

def generate_first_problem():
    """

    !! CURRENTLY NOT IN USE !!

    safely make the first problem of the session

    """
    st.session_state["game_end_time"] = time.time() + st.session_state["duration"]
    print("Making a new problem...")
    st.session_state["is_game_running"] = True
    st.session_state["is_first_problem"] = False
    new_problem()
    st.rerun()

def new_problem():
    """generate a new problem for the user"""
    print("Generating a new problem...")
    next_problem_op_, next_data_type_ = random.choice(st.session_state["active_problem_types"])
    next_problem_tag = next_problem_op_ + "_" + next_data_type_
    next_problem_op_ = OPERATOR_API_ALIASES[next_problem_op_]
    next_problem_range_ = LeftRightSliders(next_problem_tag).range()
    st.session_state["current_problem"] = CoreProblem(
        range_=next_problem_range_,
        problem_type_=next_problem_op_,
        dtype_=next_data_type_)
    st.session_state["current_problem"].calc()
    st.session_state["is_first_problem"] = False
    st.session_state["active_problem"] = True


def validate_answer(result):
    """check if user got the answer correct"""
    if result and int(result) == st.session_state["current_problem"].answer:
        return True
    else:
        return False