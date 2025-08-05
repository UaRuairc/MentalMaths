import streamlit as st
from datetime import datetime, timezone
from src.config.config_management import ConfigManager
from src.utils import get_ranges
import json


class Session:

    def __init__(self, session_id, user_id, game_mode, active_problem_types, started_at, event="game_started"):
        """

        Could do something like event=game_pause, event=game_resume, e.g. getting an ended_early=True game from the db and resuming it?

        """
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
            "answer": None,
            "keystroke_sequence": None,
            "keystroke_count": 0,
        }

        self.current_session_event = {
            "session_id": session_id,
            "user_id": user_id,
            "game_mode": game_mode,
            "active_problem_types": active_problem_types,
            "started_at": started_at,
            "ended_at": None,
            "ended_early": None,
            "num_questions": 0,
            "num_correct": 0,
            "payload": self.build_event_payload(game_mode),
            "total_keystroke_count": 0,
            "total_expected_keystroke_count": 0,
        }

    def update_problem_event(self, keystroke_sequence, keystroke_count, event="correct_answer"):
        data = {
            "problem_id": st.session_state["current_problem_id"],
            "problem_type": f"{st.session_state["current_problem"].op}_{st.session_state["current_problem"].dtype}",
            "answer_ms": st.session_state["current_problem"].time_elapsed_ms(),
            "is_correct": True,
            "created_at": str(st.session_state["current_problem"].problem_start_time),
            "left_operand": st.session_state["current_problem"].Problem.left,
            "left_operand_text":  st.session_state["current_problem"].Problem.left,
            "right_operand":  st.session_state["current_problem"].Problem.right,
            "right_operand_text":  st.session_state["current_problem"].Problem.right,
            "answer": st.session_state["current_problem"].answer,
            "keystroke_sequence": keystroke_sequence,
            "keystroke_count": keystroke_count
            }
            "left_operand_text": st.session_state["current_problem"].Problem.left,
            "right_operand": st.session_state["current_problem"].Problem.right,
            "right_operand_text": st.session_state["current_problem"].Problem.right,
            "keystroke_sequence": keystroke_sequence, "keystroke_count": keystroke_count,
            "answer": st.session_state["current_problem"].answer if event == "correct_answer" else None,
         }

        self.current_problem_event.update(data)

        self.update_session_event(event=event)

    def update_session_event(self, event="correct_answer"):
        if event=="correct_answer":
            self.current_session_event["num_questions"] += 1
            self.current_session_event["num_correct"] = st.session_state["game_score"]
            self.current_session_event["total_keystroke_count"] += len(str(self.current_problem_event["keystroke_count"]))
            self.current_session_event["total_expected_keystroke_count"] += len(str(st.session_state["current_problem"].answer))
            return

        if event=="game_completed":
            self.current_session_event["ended_at"] = st.session_state["game_end_time"]
            return

        if event=="game_ended_early":
            self.current_session_event["ended_at"] = time.time()
            self.current_session_event["ended_early"] = True
            return

    def store_problem_event(self):
        print("We would have stored the following problem in the database:")
        data_to_store = json.dumps(self.current_problem_event, indent=2, sort_keys=True, default=str)
        print(data_to_store)
        #st.session_state["supabase_client"].table("problem_events").insert(self.current_problem_event).execute()

    def store_session_event(self):
        print("We would have stored the following session in the database [note, we remove the payload config so remove verbosity for now...]:")
        event_copy = self.current_session_event.copy()
        event_copy.pop("payload")
        data_to_store = json.dumps(event_copy, indent=2, sort_keys=True, default=str)
        print(data_to_store)
        #st.session_state["supabase_client"].table("game_sessions").insert(self.current_session_event).execute()


    @staticmethod
    def build_event_payload(game_mode="standard"):
        """ Want the payload to effectively be the settings required to replicate the game state

        game mode -> standard, race, etc.

        settings -> the range on the numbers, for example.

        given the game_mode, we know the payload dictionary format

        """
        #print("about the make the payload, lets see how big the config is at this point..")

        #stats = config_stats(st.session_state["config"])
        #print({k: stats[k] for k in ("json_kib", "gzip_kib", "sha256")})

        get_val = ConfigManager.get_widget_value
        payload = {
            "version": "0.2",
            "game_mode": game_mode,
            "base_settings": {
                "active_problem_types": st.session_state["active_problem_types"],
                "duration": get_val("duration", "number_input_boxes"),
                "ranges": get_ranges(),
            },
            "extra_settings": {
                "pos_answers_only": get_val("pos_answers_only", "checkboxes"),
                "fade_problem": get_val("fade_problem", "checkboxes")
            },
        }
        payload = st.session_state["config"].copy()

        return payload





