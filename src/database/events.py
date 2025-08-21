import streamlit as st
from datetime import datetime, timezone
from src.config.config_management import ConfigManager as cm
from src.utils import get_ranges
import json
import uuid6


class GameTelemetry:

    def __init__(self, game_mode, active_problem_types, event="session_started"):
        """
        Initialize a new game session with the given parameters.
        """
        self.session_id = str(uuid6.uuid7())
        self.user_id = st.session_state["supabase_client"].auth.get_user().user.id if st.session_state.get("user") is not None else None

        self.current_problem_event={
            "event_id": None,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "problem_id": None,
            "problem_type": None,
            "is_correct": True,
            "answer_ms": None,
            "created_at": None,
            "left_num": None, # for fractions
            "left_den": None, # for fractions
            "left_operand": None,
            "right_num": None, # for fractions
            "right_den": None, # for fractions
            "right_operand": None,
            "answer": None,
            "event": event,
            "keystroke_sequence": None,
            "keystroke_count": 0,
            "status": "active",  # could be active, correct_answer, wrong_answer, duration_expired
        }
        # Could do something like event=game_pause, event=game_resume, e.g. getting an ended_early=True game from the db and resuming it?

        self.current_session_event = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "game_mode": game_mode,
            "active_problem_types": active_problem_types,
            "modifiers": None,
            "started_at": str(datetime.now(timezone.utc)),
            "ended_at": None,
            "ended_early": False,
            "num_questions": 0,
            "num_correct": 0,
            "payload": None,
            "total_keystroke_count": 0,
            "total_expected_keystroke_count": 0,
            "event": None,
            "status": "active",  # could be active, ended or ended_early
        }

        try:
            print("not storing right now")
            # self.send_initial_session_event()
        except Exception as e:
            print(f"Error storing session event: {e}")
            res = None


    def update_problem_event(self, keystroke_sequence, keystroke_count, event="correct_answer"):

        if event == "problem_created":
            self.reset_problem_event()

        problem_snapshot = st.session_state["current_problem"].snapshot(event)

        data = {
            "event_id": str(uuid6.uuid7()),
            "problem_id": st.session_state["current_problem_id"],
            "keystroke_sequence": keystroke_sequence, "keystroke_count": keystroke_count,
         }

        data.update(problem_snapshot)



        self.current_problem_event.update(data)

        self.update_session_event(event=event)

    def update_session_event(self, event="correct_answer"):

        if event == "session_started":
            self.current_session_event["total_expected_keystroke_count"] += len(
                str(st.session_state["current_problem"].answer)) if event in ("correct_answer", "wrong_answer") else 0
            self.current_session_event["modifiers"] = st.session_state["current_problem"].modifiers
            self.current_session_event["status"] = event

        self.current_session_event["num_questions"] += 1 if event in ("correct_answer", "wrong_answer") else 0
        self.current_session_event["num_correct"] = st.session_state["game_score"]

        self.current_session_event["total_keystroke_count"] += self.current_problem_event["keystroke_count"] if event in ("correct_answer", "wrong_answer") else 0
        self.current_session_event["total_expected_keystroke_count"] += len(
            str(st.session_state["current_problem"].answer)) if event in ("correct_answer", "wrong_answer") else 0

        self.current_session_event["modifiers"] = st.session_state["current_problem"].modifiers
        self.current_session_event["status"] = "active" if event in ("correct_answer", "wrong_answer") else event
        self.current_session_event["ended_at"] = (str(datetime.now(timezone.utc))) if self.current_session_event["status"] != "active" else None
        self.current_session_event["payload"] = self.build_event_payload()
        if event == "game_ended_early":
            self.current_session_event["ended_early"] = True
        return

    def store_problem_event(self, event=None):
        print("We would have stored the following problem in the database:")
        data_to_store = json.dumps(self.current_problem_event, indent=2, sort_keys=True, default=str)
        #print(data_to_store)
        try:
            print("not storing right now")
            # res = st.session_state["supabase_client"].schema("api").from_("problem_events").insert(self.current_problem_event).execute()
        except Exception as e:
            print(f"Error storing problem event: {e}")
            res = None
            return None
        #st.session_state["supabase_client"].table("problem_events").insert(self.current_problem_event).execute()

    def store_session_event(self, event=None):
        print("We would have stored the following session in the database:")
        event_copy = self.current_session_event.copy()
        data_to_store = json.dumps(event_copy, indent=2, sort_keys=True, default=str)
        #print(data_to_store)
        try:
            print("not storing right now")
            print(self.current_session_event)

            #res = st.session_state["supabase_client"].schema("api").from_("game_sessions").insert(self.current_session_event).execute()
        except Exception as e:
            print(f"Error storing session event: {e}")
            res = None



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

        get_val = cm.get_widget_value
        payload = {
            "version": "0.2",
            "game_mode": game_mode,
            "base_settings": {
                "active_problem_types": st.session_state["active_problem_types"],
                "duration": get_val("duration", "number_input_boxes"),
                "ranges": get_ranges(),
            },
            "modifiers": st.session_state["current_problem"].modifiers
        }
        # payload = st.session_state["config"].copy()

        return payload

    def reset_problem_event(self):
        self.current_problem_event = {
            "session_id": self.current_problem_event["session_id"],
            "user_id": self.current_problem_event["user_id"],
            "problem_id": None,
            "problem_type": None,
            "is_correct": True,
            "answer_ms": None,
            "created_at": None,
            "left_num": None,
            "left_den": None,
            "left_operand": None,
            "right_num": None,
            "right_den": None,
            "right_operand": None,
            "answer": None,
            "keystroke_sequence": None,
            "keystroke_count": 0,
            "status": "reset",
            "event": "reset"
        }

    def send_initial_session_event(self):
        """
        Send the initial session event to the database.
        """
        self.update_session_event(event="session_started")
        self.store_problem_event(event="session_started")
        return




