import time
import streamlit as st
from src.database.events import GameTelemetry
from src.problem_management.problem_generation import new_problem
from src.problem_management.problem_engine import Question
import random
from src.utils import get_range



def start_game(event="game_started"):
    print("Starting the game.")
    st.session_state["game_start_time"] = time.time()
    st.session_state["game_end_time"] = st.session_state["game_start_time"] + st.session_state["config"]["number_input_boxes"]["duration"]["value"]

    st.session_state["GameTelemetry"] = GameTelemetry(
        game_mode="standard",
        active_problem_types=st.session_state["active_problem_types"],
        event=event
    )
    new_problem()
    st.session_state["is_game_running"] = True
    st.session_state["game_score"] = 0
    st.rerun()


def end_game(event="game_ended_early"):
    """end game: currently sends user to setup page (later, optional results / feedback page will be added?)"""
    st.session_state["GameTelemetry"].update_problem_event(keystroke_count=0, keystroke_sequence="", event=event)
    print("Ending the game.")
    st.session_state["GameTelemetry"].store_problem_event()
    st.session_state["GameTelemetry"].store_session_event()
    st.session_state["is_game_running"] = False
    st.rerun()

@st.fragment(run_every=2)
def game_countdown_timer(verbosity=1):
    """
    Right now, we are printing debug statements. So, run_every= 2 seconds to prevent verbose output
    Will need to make a game logger helper soon
    """
    #debug_fragment_info("Game Timer")

    if st.session_state["is_game_running"]:
        time_remaining = st.session_state["game_end_time"] - time.time()
        time_run_out = time_remaining <= 0
        if verbosity == 1: print(f"Time remaining: {time_remaining}")

        if time_run_out :
            if verbosity == 1: print("Game has ended.")
            end_game(event="game_completed")

class Game():

    def __init__(self, event="game_session_started"):
        self.is_running = False
        self.start_time = None
        self.end_time = None
        self.score = 0
        self.problem_id = 0
        self.last_event = event
        self.last_user_response = None
        self.score = 0
        self.ops = ["add", "subtract", "mult", "div"]
        self.op_API_ALIASES = {
            "add": "add",
            "subtract": "sub",
            "mult": "mult",
            "div": "div"
        }
        self.Question = None
        self.current_problem_id = None
        self.current_problem_type = None
        self.GameTelemetry = None

        self.init_telemetry(event=event)

    def init_telemetry(self, event):
        if self.GameTelemetry is None:
            print("Initialising telemetry.")
            self.start_time = time.time()
            self.end_time = self.start_time + st.session_state["config"]["number_input_boxes"]["duration"]["value"]
            self.is_running = True
            st.session_state["is_game_running"] = self.is_running
            self.score = 0
            st.session_state["game_score"] = self.score

            self.GameTelemetry = GameTelemetry(
                game_mode="standard",
                active_problem_types=st.session_state["active_problem_types"],
                event=event
            )
            st.session_state["GameTelemetry"] = self.GameTelemetry

            self.create_new_problem()
        else:
            print("telemetry already initialised.")

    def end_game(self):
        if self.is_running:
            self.handle_event()
            st.rerun()

        print("The game is not running, cannot end the game session.")
        return


    def handle_event(self):

        if self.last_event == "game_session_started":
            self.GameTelemetry.reset_problem_event()
            self.GameTelemetry.update_problem_event(keystroke_sequence=0, keystroke_count=0, event=self.last_event)
            self.last_event = "first_problem_created"
            return

        if self.last_event == "user_answer_validated":
            self.score += 1
            st.session_state["game_score"] = self.score
            self.problem_id += 1
            st.session_state["problem_id"] = self.problem_id
            # print(f"the user response was: {user_response}")
            self.GameTelemetry.update_problem_event(keystroke_sequence=self.last_user_response[2],
                                                                          keystroke_count=self.last_user_response[3],
                                                                          event=self.last_event)
            # print(st.session_state["GameTelemetry"].current_problem_event)
            # print(json.dumps(st.session_state["GameTelemetry"].current_session_event, indent=2, default=str))
            self.GameTelemetry.store_problem_event()
            self.last_event = "problem_answered_correctly"
            return

        if self.last_event == "game_ended_early":
            print("The game ended early.")
            self.GameTelemetry.update_problem_event(keystroke_count=0, keystroke_sequence="", event=self.last_event)
            self.GameTelemetry.store_problem_event()
            self.GameTelemetry.store_session_event()
            self.is_running = False
            st.session_state["is_game_running"] = self.is_running
            return

        if self.last_event == "game_timed_out":
            print("The game timed out.")
            self.GameTelemetry.update_problem_event(keystroke_count=0, keystroke_sequence="", event=self.last_event)
            self.GameTelemetry.store_problem_event()
            self.GameTelemetry.store_session_event()
            self.is_running = False
            st.session_state["is_game_running"] = self.is_running
            return



        return

    def create_new_problem(self):
        self.GameTelemetry.reset_problem_event()
        self.new_problem()
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
            return valid

        else:
            self.last_event = "user_answer_invalidated"
            return False





    def new_problem(self):
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


    @staticmethod
    def get_modifiers():
        return {
            "pos_answers_only": st.session_state["config"]["checkboxes"]["pos_answers_only"]["value"],
            "fade_problem": st.session_state["config"]["checkboxes"]["fade_problem"]["value"],
    }






