import time
import streamlit as st
from src.game.content.modifiers import ModManager as mm
from src.config.config_management import WidgetRegistry
from src.database.telemetry import GameTelemetry
from src.game.content.problem_engine import Question
import random
from src.utils import get_range
from datetime import datetime, timezone, timedelta
from src.game.content.session_tagger import update_session_tags
from dataclasses import dataclass, field, asdict
from typing import Optional

def start_game():
    st.session_state["Game"] = Game()
    st.rerun()

@st.fragment(run_every=2)
def game_countdown_timer(verbosity=0):
    """
    Right now, we are printing debug statements. So, run_every= 2 seconds to prevent verbose output
    Will need to make a game logger helper soon
    """
    #debug_fragment_info("Game Timer")
    game = st.session_state["Game"]

    if game.is_running:
        timed_out = game.check_timeout()
        if verbosity == 1: print(f"Time elapsed: {time.perf_counter() - game.start_perf_counter}")

        if timed_out:
            if verbosity == 1: print("Game has ended.")
            game.last_event = "game_timed_out"


@dataclass
class GameStats:
    num_questions: int = 0
    num_correct: int = 0
    score: int = 0
    total_keystroke_count: int = 0
    total_expected_keystroke_count: int = 0
    mods_seen: set = field(default_factory=set)
    mods_activated: set = field(default_factory=set)

    start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    ended_early: bool = False

    def to_dict(self):
        return asdict(self)

    def get_payload(self):
        stats = self.to_dict()
        stats["mods_seen"] = list(self.mods_seen)
        stats["mods_activated"] = list(self.mods_activated)
        stats["started_at"] = stats.pop("start_time")
        stats["ended_at"] = stats.pop("actual_end_time")
        stats.pop("scheduled_end_time")
        return stats

class Game:

    def __init__(self):
        self.active_problem_types=st.session_state["active_problem_types"]
        self.game_duration = WidgetRegistry.get_widget_value("duration", "number_input_box")

        self.stats = GameStats()
        self.is_running: bool = False
        self.start_perf_counter = None

        self.Question = None
        self.GameTelemetry = None
        self.last_user_response = None # will be a list: [user_answer, question_id, keystroke_sequence, keystroke_count]
        self.ops = ["add", "subtract", "mult", "div"]
        self.op_API_ALIASES = {
            "add": "add",
            "subtract": "sub",
            "mult": "mult",
            "div": "div"
        }

        self.event_history = []
        self.mod_log = {}
        self.tags = {}

        st.session_state["game_score"] = self.stats.score
        st.session_state["is_game_running"] = self.is_running

        self._last_event = None
        self.last_event = "game_session_initialised"

    def start(self):
        self.is_running = True
        st.session_state["is_game_running"] = self.is_running
        self.stats.start_time = datetime.now(timezone.utc)
        self.start_perf_counter = time.perf_counter()
        self.stats.scheduled_end_time = self.stats.start_time + timedelta(seconds=self.game_duration)
        self.init_telemetry()
        self.next_question()

    def stop(self):
        self.is_running = False
        self.stats.actual_end_time = datetime.now(timezone.utc)
        st.session_state["is_game_running"] = self.is_running
        self.stats.ended_early = (self.last_event != "game_timed_out")

    @property
    def last_event(self):
        return self._last_event

    @last_event.setter
    def last_event(self, event):

        if event != self._last_event or event == "button_interaction":
            print(f"Event transition: {self.last_event} -> {event}")
            self._last_event = event
            self.event_history.append(event)
            #print(f"Event history: {self.event_history}")
            self.handle_event()

    def init_telemetry(self):
        if self.GameTelemetry is None:
            print("Initialising telemetry.")
            self.GameTelemetry = GameTelemetry(
                event=self.last_event
            )
            self.GameTelemetry.new_session_payload(record_last_payload=False, data=self.session_snapshot())
        else:
            print("telemetry already initialised.")


    def handle_event(self):

        """
        Handles game events based on the last emitted event, updating telemetry, session state, and game logic
        accordingly. Executes logic specific to each game event type to maintain proper game state and telemetry
        synchronization.
        """

        if self.last_event == "game_session_initialised":
            self.start()
            return

        if self.last_event in ["initial_question_created", "new_question_created"]:
            self.mod(targets=[self])
            self.Question.Problem.solve()
            self.Question.answer = self.Question.Problem.eff_answer
            self.GameTelemetry.new_problem_payload(record_last_payload=(self.last_event == "new_question_created"), data=self.Question.snapshot(last_event=self.last_event))
            return

        if self.last_event in ["user_pressed_end_game", "game_timed_out"]:
            self.stop()

        if self.last_event == "user_answer_validated":
            self.stats.num_correct += 1
            st.session_state["game_score"] = self.stats.num_correct

        if self.last_event in ["user_answer_validated", "game_timed_out", "user_pressed_end_game"]:
            problem_snapshot = self.Question.snapshot(last_event=self.last_event)
            problem_update = {
                "is_correct": (self.last_event == "user_answer_validated"),
                "event": self.last_event,
                "keystroke_sequence": self.last_user_response[2] if self.last_user_response else "",
                "keystroke_count": self.last_user_response[3] if self.last_user_response else 0,
                "status": self.last_event,
            }
            data = {**problem_snapshot, **problem_update}

            self.GameTelemetry.current_problem_payload.update(data)
            update_session_tags(self, self.Question.Problem.eff_tag_info)
            snapshot = self.session_snapshot()
            session_update = {
                "payload": self.GameTelemetry.build_event_payload(),
                "status": self.last_event,
                **snapshot
            }
            self.GameTelemetry.current_session_payload.update(session_update)


        if self.last_event == "user_answer_validated":
            self.next_question()
            st.rerun()

        if self.last_event == "user_answer_invalidated":
            st.rerun()

        if self.last_event == "button_interaction":
        #if payload["button"] == "reveal_problem":
        # there is currently only one button dependent modifier, we will do this for now.
            self.mod(targets=[self])
            return

        if self.last_event in ["game_timed_out", "user_pressed_end_game"]:
            self.last_event = "session_ended"
            st.rerun()

        if self.last_event == "session_ended":
            self.GameTelemetry.record("session")
            self.last_event = self.GameTelemetry.commit(event=self.last_event)

        if self.last_event in ["session_committed", "session_commit_skipped"]:
            pass

        return

    def validate_answer(self, user_response):
        """check if user got the answer correct"""

        if not user_response or user_response == self.last_user_response:
            return

        self.last_user_response = user_response
        user_answer, question_id, _, _ = self.last_user_response

        if self.Question.q_type == "standard":
            # there's a 1 to 1 correspondence between question_id and problem_id for standard question types
            # only the standard question types exist at this moment
            correct_id = self.Question.Problem.id
            correct_answer = self.Question.answer
        else:
            NotImplementedError("Unsupported question type")


        valid = (int(user_answer) == correct_answer) and (question_id == correct_id)

        self.last_event = "user_answer_validated" if valid else "user_answer_invalidated"

    def next_question(self, q_type="standard"):
        next_problem_op_, next_data_type_ = random.choice(st.session_state["active_problem_types"])
        next_problem_tag = next_problem_op_ + "_" + next_data_type_

        self.Question = Question(
            range_=get_range(next_problem_tag),
            op_=self.op_API_ALIASES[next_problem_op_],
            dtype_=next_data_type_,
            q_type_=q_type
        )

        self.Question.prepare(self.stats.num_questions+1)
        self.stats.num_questions += 1
        if self.last_user_response is not None:
            self.stats.total_keystroke_count += self.last_user_response[3]
        self.stats.total_expected_keystroke_count += len(str(self.Question.answer))
        st.session_state["fade_class_identifier"] += 1
        self.last_event = "initial_question_created" if self.stats.num_questions == 1 else "new_question_created"
        return

    def session_snapshot(self):

        stats = self.stats.get_payload()
        data = {
            **stats,
            "game_mode": "standard",
            "active_problem_types": self.active_problem_types,
            "mod_log": self.mod_log,
            "event_history": self.event_history,
            "left_tags": self.tags.get("left", None),
            "right_tags": self.tags.get("right", None),
            "ans_tags": self.tags.get("ans", None),
            "operator_tags": self.tags.get("operator", None),
            "general_tags": self.tags.get("general", None),
        }

        return data

    def check_timeout(self):
        return datetime.now(timezone.utc) > self.stats.scheduled_end_time

    def mod(self, targets: list):
        for target in targets:
            seen, activated, cascade_targets = mm.mod(self.last_event, target=target)
            self.stats.mods_seen |= seen
            self.stats.mods_activated |= activated

            if cascade_targets:
                self.mod(targets = cascade_targets)
            else:
                return
