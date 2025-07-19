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

def new_problem():
    """generate a new problem for the user"""
    next_problem_op_, next_data_type_ = random.choice(st.session_state["active_problem_types"])
    next_problem_tag = next_problem_op_ + "_" + next_data_type_

    # WARNING: Currently the CoreProblem class can be pickled. If it ever can't be,
    # then just store the required data in a map and put that in the session state. For now, this is convenient though
    st.session_state["current_problem"] = CoreProblem(
        range_=get_range(next_problem_tag),
        problem_type_=OPERATOR_API_ALIASES[next_problem_op_],
        dtype_=next_data_type_,
        positive_answers_only_=st.session_state["config"]["checkboxes"]["pos_answers_only"]["value"])

    st.session_state["current_problem"].calc()
    st.session_state["fade_class_identifier"] += 1
    st.session_state["game_score"] += 1
    st.session_state["problem_id"] += 1
    st.session_state["current_problem_id"] = st.session_state["problem_id"]


def validate_answer(user_response: list | str):
    """check if user got the answer correct"""
    if user_response == "":
        return False

    user_answer, problem_id = user_response

    correct_answer = st.session_state["current_problem"].answer
    correct_problem_id = st.session_state["current_problem_id"]

    return (int(user_answer) == correct_answer) and (problem_id == correct_problem_id)

def get_range(next_problem_tag):
    boxes_config = st.session_state["config"]["number_input_boxes"]
    if next_problem_tag != "div_ints":
        #(l1, r1) + (l2, r2) = ?
        l1 = boxes_config[f"first_{next_problem_tag}_operand_range_left"]["value"]
        r1 = boxes_config[f"first_{next_problem_tag}_operand_range_right"]["value"]
        l2 = boxes_config[f"second_{next_problem_tag}_operand_range_left"]["value"]
        r2 = boxes_config[f"second_{next_problem_tag}_operand_range_right"]["value"]
    else:
        # (l1, r1) + (l2, r2) = ...
        l1 = boxes_config[f"second_{next_problem_tag}_operand_range_left"]["value"]
        r1 = boxes_config[f"second_{next_problem_tag}_operand_range_right"]["value"]
        l2 = boxes_config[f"answer_{next_problem_tag}_range_left"]["value"]
        r2 = boxes_config[f"answer_{next_problem_tag}_range_right"]["value"]
    range1 = (l1, r1)
    range2 = (l2, r2)

    return range1, range2
