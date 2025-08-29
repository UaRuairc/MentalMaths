import time
import streamlit as st
from src.config.config_management import ConfigManager as cm
from src.database.telemetry import GameTelemetry
from src.problem_management.problem_engine import Question
import random
from src.utils import get_range
from datetime import datetime, timezone, timedelta


def start_game(event="game_session_started"):
    st.session_state["Game"] = Game(event=event)
    st.rerun()

def end_game(event="game_ended_early"):
    """end game: currently sends user to setup page (later, optional results / feedback page will be added?)"""
    st.session_state["Game"].last_event = event
    st.rerun()

def start_game_old(event="game_started"):
    print("Starting the game.")
    st.session_state["game_start_time"] = time.time()
    st.session_state["game_end_time"] = st.session_state["game_start_time"] + cm.get_widget_value("duration", "number_input_boxes")

    st.session_state["GameTelemetry"] = GameTelemetry(
        game_mode="standard",
        active_problem_types=st.session_state["active_problem_types"],
        event=event
    )
    new_problem()
    st.session_state["is_game_running"] = True
    st.session_state["game_score"] = 0
    st.rerun()


def end_game_old(event="game_ended_early"):
    """end game: currently sends user to setup page (later, optional results / feedback page will be added?)"""
    st.session_state["GameTelemetry"].update_problem_event(keystroke_count=0, keystroke_sequence="", event=event)
    print("Ending the game.")
    #st.session_state["GameTelemetry"].store_problem_event()
    #st.session_state["GameTelemetry"].store_session_event()
    st.session_state["is_game_running"] = False
    st.rerun()

@st.fragment(run_every=2)
def game_countdown_timer(verbosity=1):
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

class Game:

    def __init__(self, event="game_session_started"):
        self.is_running = False
        self.start_time = None
        self.start_perf_counter = None
        self.duration_in_seconds = cm.get_widget_value("duration", "number_input_boxes")
        self.scheduled_end_time = None
        self.actual_end_time = None
        self.ended_early = False
        self.num_questions = 0
        self.num_correct = 0
        #self.score = 0
        #self.score = 0
        st.session_state["is_game_running"] = self.is_running
        st.session_state["game_score"] = self.num_correct
        self.problem_id = 0 # this is just a number used to sync between the custom widget and streamlit, so we don't validate the same problem twice
        self.total_keystroke_count = 0
        self.total_expected_keystroke_count = 0
        self.last_user_response = None # will be a list: [user_answer, problem_id, keystroke_sequence, keystroke_count]
        self.ops = ["add", "subtract", "mult", "div"]
        self.op_API_ALIASES = {
            "add": "add",
            "subtract": "sub",
            "mult": "mult",
            "div": "div"
        }
        self.active_problem_types = st.session_state["active_problem_types"]
        self.Question = None
        self.current_problem_id = None # if we create a new problem with a new problem id, but the same answer as the last problem, the different problem_id will prevent any buggy double validation
        self.current_problem_type = None
        self.GameTelemetry = None
        self.event_history = []


        self._last_event = None

        self.last_event = event



    @property
    def last_event(self):
        return self._last_event

    @last_event.setter
    def last_event(self, event):

        if event != self._last_event:
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
            st.session_state["GameTelemetry"] = self.GameTelemetry
        else:
            print("telemetry already initialised.")

    def end_game(self):
        if self.is_running:
            self.handle_event()


        print("The game is not running, cannot end the game session.")
        return


    def handle_event(self):

        """
        Handles game events based on the last emitted event, updating telemetry, session state, and game logic
        accordingly. Executes logic specific to each game event type to maintain proper game state and telemetry
        synchronization.

        Typical flow:

        game_session_started -> initial_problem_created -> user_answer_validated/new_problem_created (repeats) -> game_timed_out/user_pressed_end_game

        or

        user_answer_invalidated -> user_answer_validated/new_problem_created (repeats) -> game_timed_out/user_pressed_end_game
        """

        if self.last_event == "game_session_started":
            self.start_time = datetime.now(timezone.utc)
            self.start_perf_counter = time.perf_counter()
            self.scheduled_end_time = self.start_time + timedelta(seconds=self.duration_in_seconds)
            self.is_running = True
            st.session_state["is_game_running"] = self.is_running

            self.init_telemetry()
            self.GameTelemetry.new_session_payload(record_last_payload=False, data=self.session_snapshot())

            self.create_new_problem()
            return

        if self.last_event == "initial_problem_created":
            self.GameTelemetry.new_problem_payload(record_last_payload=False, problem_id=self.problem_id, data=self.Question.snapshot(last_event=self.last_event))
            return

        if self.last_event == "new_problem_created":
            self.total_expected_keystroke_count += len(str(self.Question.answer))
            self.GameTelemetry.new_problem_payload(record_last_payload=True, problem_id=self.problem_id, data=self.Question.snapshot(last_event=self.last_event))
            return

        if self.last_event == "user_answer_validated":
            self.num_correct += 1
            self.problem_id += 1 # this is just a number used to sync between the custom widget and streamlit, so we don't validate the same problem twice
            self.total_keystroke_count += self.last_user_response[3]
            st.session_state["problem_id"] = self.problem_id
            st.session_state["game_score"] = self.num_correct

            problem_snapshot = self.Question.snapshot(last_event=self.last_event)
            problem_update = {
                "keystroke_sequence": self.last_user_response[2],
                "keystroke_count": self.last_user_response[3],
                "status": self.last_event,
            }
            data = {**problem_snapshot, **problem_update}
            self.GameTelemetry.current_problem_payload.update(data)

            session_update = self.session_snapshot()

            self.GameTelemetry.current_session_payload.update(session_update)

            self.create_new_problem()
            st.rerun()
            return

        if self.last_event == "user_answer_invalidated":
            return



        if self.last_event in ["game_timed_out", "user_pressed_end_game"]:
            self.ended_early = True if self.last_event == "user_pressed_end_game" else False
            self.actual_end_time = datetime.now(timezone.utc)
            # the last problem event was never updatd or recorded, so
            problem_update = {
                "is_correct": False,
                "event": self.last_event,
                "keystroke_sequence": self.last_user_response[2],
                "keystroke_count": self.last_user_response[3],
                "status": self.last_event
            }
            self.GameTelemetry.current_problem_payload.update(problem_update)

            session_update = {
                    "payload": self.GameTelemetry.build_event_payload(),
                    "status": self.last_event
            }

            snapshot = self.session_snapshot()
            session_update = {**session_update, **snapshot}
            self.GameTelemetry.current_session_payload.update(session_update)
            self.GameTelemetry.record("session")

            self.is_running = False
            st.session_state["is_game_running"] = self.is_running
            self.GameTelemetry.send()
            st.rerun()

        return

    def create_new_problem(self):
        self.generate_new_problem()
        self.total_expected_keystroke_count += len(str(self.Question.answer))

        if self.last_event == "game_session_started":

            self.last_event = "initial_problem_created"
        else:
            self.last_event = "new_problem_created"



    def validate_answer(self):
        """check if user got the answer correct"""
        if not self.last_user_response:
            return False

        user_answer, problem_id, _, _ = self.last_user_response
        correct_answer = self.Question.answer
        correct_problem_id = self.problem_id

        valid = (int(user_answer) == correct_answer) and (problem_id == correct_problem_id)


        if valid:
            self.last_event = "user_answer_validated"
            return True

        else:
            self.last_event = "user_answer_invalidated"
            return True





    def generate_new_problem(self):
        """generate a new problem for the user"""
        next_problem_op_, next_data_type_ = random.choice(st.session_state["active_problem_types"])
        next_problem_tag = next_problem_op_ + "_" + next_data_type_

        self.Question = Question(
            range_=get_range(next_problem_tag),
            op_=self.op_API_ALIASES[next_problem_op_],
            dtype_=next_data_type_,
            modifiers=self.get_modifiers()
        )

        st.session_state["current_problem"] = self.Question

        self.Question.calc()
        st.session_state["fade_class_identifier"] += 1
        self.current_problem_id = self.problem_id
        self.current_problem_type = self.Question.op
        st.session_state["current_problem_id"] = self.current_problem_id
        st.session_state["current_problem_type"] = self.current_problem_type
        self.num_questions += 1
        return

    @staticmethod
    def get_modifiers():
        return {
            "pos_answers_only":  cm.get_widget_value("pos_answers_only", "checkboxes"),
            "fade_problem": cm.get_widget_value("fade_problem", "checkboxes")
    }


    def update(self, score, problem_id, last_user_response):
        self.score = score
        self.problem_id = problem_id
        self.last_user_response = last_user_response

    def session_snapshot(self):

        data = {
            "game_mode": "standard",
            "active_problem_types": self.active_problem_types,
            "modifiers": self.get_modifiers(),
            "started_at": str(self.start_time),
            "ended_at": str(self.actual_end_time),
            "ended_early": self.ended_early,
            "event_history": self.event_history,
            "num_questions": self.num_questions,
            "num_correct": self.num_correct,
            "total_keystroke_count": self.total_keystroke_count,
            "total_expected_keystroke_count": self.total_expected_keystroke_count,
        }

        return data

    def check_timeout(self):
        return datetime.now(timezone.utc) > self.scheduled_end_time







