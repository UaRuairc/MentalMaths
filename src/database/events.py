import streamlit as st
from datetime import datetime, timezone
from src.config.config_management import ConfigManager as cm
from src.utils import get_ranges
import json
import uuid6
from dataclasses import dataclass, field, fields, replace, asdict
from typing import Any, Optional
from collections import deque


@dataclass
class ProblemData:
    event_id: Optional[str]
    session_id: str
    user_id: str
    problem_id: int
    event: str
    created_at: Optional[str]
    problem_type: Optional[str]

    left_num: Optional[int] = None
    left_den: Optional[int] = None
    left_operand: Optional[float] = None
    right_num: Optional[int] = None
    right_den: Optional[int] = None
    right_operand: Optional[float] = None
    answer: Optional[float] = None
    is_correct: Optional[bool] = None
    answer_ms: Optional[int] = None
    modifiers: Optional[Any] = None

    keystroke_sequence: Optional[str] = None
    keystroke_count: Optional[int] = 0
    status: str = "active"

    def to_dict(self):
        return asdict(self)

    def update(self, data: dict):
        allowed_data = {field_.name for field_ in fields(self)}
        disallowed_data = data.keys() - allowed_data
        if disallowed_data:
            raise ValueError(f"Invalid fields for ProblemEvent: {disallowed_data}")

        # need to
        # figure out when we should update, and what we should do it,


        for key, value in data.items():
            setattr(self, key, value)

        return self

@dataclass
class SessionData:
    session_id: str
    user_id: str
    game_mode: str
    active_problem_types: list
    modifiers: Optional[Any]
    started_at: str

    ended_at: Optional[str] = None
    ended_early: bool = False
    num_questions: int = 0
    num_correct: int = 0
    payload: Optional[Any] = None
    event_history: Optional[list] = None
    total_keystroke_count: int = 0
    total_expected_keystroke_count: int = 0
    status: str = "active"

    def to_dict(self):
        return asdict(self)

    def update(self, data: dict):
        allowed_data = {field_.name for field_ in fields(self)}
        disallowed_data = data.keys() - allowed_data
        if disallowed_data:
            raise ValueError(f"Invalid fields for ProblemEvent: {disallowed_data}")

        # need to
        # figure out when we should update, and what we should do it,


        for key, value in data.items():
            setattr(self, key, value)

        return self

class GameTelemetry:

    def __init__(self, event="session_started"):
        """
        Initialize a new game session with the given parameters.
        """
        self.session_id = str(uuid6.uuid7())
        self.supabase_session_id = None
        self.user_id = st.session_state["supabase_client"].auth.get_user().user.id if st.session_state.get("user") is not None else None
        self.session_event_buffer = None
        self.problem_event_buffer = []
        self.current_problem_payload = None
        self.current_session_payload = None

        try:
            print("not storing right now")
            # self.send_initial_session_event()
        except Exception as e:
            print(f"Error storing session event: {e}")
            res = None


    def new_problem_payload(self, record_last_payload, problem_id, data):

        if record_last_payload and self.current_problem_payload is not None:
            self.record("problem")

        self.current_problem_payload = ProblemData(
            event_id = str(uuid6.uuid7()),
            session_id = self.session_id,
            user_id = self.user_id,
            problem_id=problem_id,
            **data
        )

    def new_session_payload(self, record_last_payload, data):

        if record_last_payload and self.current_session_payload is not None:
            self.current_session_payload.status = "ended"
            self.record("session")

        self.current_session_payload = SessionData(
            session_id=self.session_id,
            user_id=self.user_id,
            **data
        )

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

    def record(self, payload_type):

        if payload_type == "session":
            self.session_event_buffer = self.current_session_payload
        elif payload_type == "problem":
            self.problem_event_buffer.append(self.current_problem_payload)

    def send(self):
        failed = False
        if self.session_event_buffer:
            next_payload = self.session_event_buffer
            next_payload = next_payload.to_dict()
            try:

                res = (
                    st.session_state["supabase_client"]
                    .schema("api")
                    .from_("game_sessions")
                    .insert(next_payload)
                    .execute()
                    )

            except Exception as e:
                print(f"Error storing session event: {e}")
                failed = True
                res = None

        while self.problem_event_buffer:

            BATCH_SIZE = 100
            next_payload_batch = self.problem_event_buffer[:BATCH_SIZE]
            next_payload_batch = [payload.to_dict() for payload in next_payload_batch]
            self.problem_event_buffer = self.problem_event_buffer[BATCH_SIZE:]

            try:
                res = (
                    st.session_state["supabase_client"]
                    .schema("api")
                    .from_("problem_events")
                    .insert(next_payload_batch)
                    .execute()
                )

            except Exception as e:
                print(f"Error storing problem event: {e}")
                failed = True
                res = None













