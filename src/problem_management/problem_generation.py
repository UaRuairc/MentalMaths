import streamlit as st
import random
from src.problem_management.problem_engine import Question
from src.utils import get_range

ops = ["add", "subtract", "mult", "div"]
op_API_ALIASES = {
    "add": "add",
    "subtract": "sub",
    "mult": "mult",
    "div": "div"
}

def new_problem():
    """generate a new problem for the user"""
    next_problem_op_, next_data_type_ = random.choice(st.session_state["active_problem_types"])
    next_problem_tag = next_problem_op_ + "_" + next_data_type_

    # WARNING: Currently the CoreProblem class can be pickled. If it ever can't be,
    # then just store the required data in a map and put that in the session state. For now, this is convenient though
    st.session_state["current_problem"] = Question(
        range_=get_range(next_problem_tag),
        op_=op_API_ALIASES[next_problem_op_],
        dtype_=next_data_type_,
        positive_answers_only_=st.session_state["config"]["checkboxes"]["pos_answers_only"]["value"]
    )

    st.session_state["current_problem"].calc()
    st.session_state["fade_class_identifier"] += 1
    st.session_state["game_score"] += 1
    st.session_state["problem_id"] += 1
    st.session_state["current_problem_id"] = st.session_state["problem_id"]
    st.session_state["current_problem_type"] = st.session_state["current_problem"].op


def validate_answer(user_response: list | str):
    """check if user got the answer correct"""
    if user_response == "":
        return False

    user_answer, problem_id = user_response

    correct_answer = st.session_state["current_problem"].answer
    correct_problem_id = st.session_state["current_problem_id"]

    return (int(user_answer) == correct_answer) and (problem_id == correct_problem_id)


