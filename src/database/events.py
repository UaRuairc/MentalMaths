import streamlit as st
import time
from src.config.config_management import ConfigManager
from src.utils import get_ranges


class Session:

    def __init__(self, session_id, user_id, game_mode, active_problem_types, started_at):
        self.current_problem_event={
            "session_id": session_id,
            "user_id": user_id,
            "problem_id": None,
            "problem_type": None,
            "is_correct": True,
            "answer_ms": None,
            "created_at": None,
            "left_num": None,
            "left_den": None,
            "left_operand": None,
            "left_operand_text": None,
            "right_num": None,
            "right_den": None,
            "right_operand": None,
            "right_operand_text": None,
            "answer": None
        }

        self.current_session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "game_mode": game_mode,
            "active_problem_types": active_problem_types,
            "started_at": started_at,
            "ended_at": None,
            "ended_early": None,
            "num_questions": None,
            "num_correct": None,
            "payload": self.build_payload(game_mode),
        }

    def collect_problem_data(self):
        data = {
            "problem_id": st.session_state["current_problem_id"],
            "problem_type": f"{st.session_state["current_problem"].op}_{st.session_state["current_problem"].dtype}",
            "answer_ms": (time.time() - st.session_state["current_problem"].problem_start_time)*1000,
            "is_correct": True,
            "created_at": st.session_state["current_problem"].problem_start_time,
            "left_operand": st.session_state["current_problem"].Problem.left,
            "left_operand_text":  st.session_state["current_problem"].Problem.left,
            "right_operand":  st.session_state["current_problem"].Problem.right,
            "right_operand_text":  st.session_state["current_problem"].Problem.right,
            "answer": st.session_state["current_problem"].answer,
            }

        self.current_problem_event.update(data)

        self.update_session_data()


    def store_problem_data(self):
        st.session_state["supabase_client"].table("problem_events").insert(self.current_problem_event).execute()


    def store_session_data(self):
        st.session_state["supabase_client"].table("game_sessions").insert(self.current_session_data).execute()

    def update_session_data(self, ending: bool = False):
        self.current_session_data["num_questions"] = st.session_state["game_score"]
        self.current_session_data["num_correct"] = st.session_state["game_score"]

        if ending:
            self.current_session_data["ended_at"] = st.session_state["game_end_time"]

    @staticmethod
    def build_payload(game_mode="standard"):
        """ Want the payload to effectively be the settings required to replicate the game state

        game mode -> standard, race, etc.

        settings -> the range on the numbers, for example.

        given the game_mode, we know the payload dictionary format

        """

        get_val = ConfigManager.get_widget_value
        payload = {
            "version": "0.2",
            "game_mode": game_mode,
            "base_settings": {
                "active_problem_types": st.session_state["active_problem_types"],
                "duration": get_val("number_input_boxes", "duration"),
                "ranges": get_ranges("number_input_boxes"),
            },
            "extra_settings": {
                "pos_answers_only": get_val("checkboxes", "pos_answers_only"),
                "fade_problem": get_val("checkboxes", "fade_problem")
            },
        }

        return payload





