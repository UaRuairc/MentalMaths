import streamlit as st

from src.database.connection import init_connection
from src.ui.widgets.registry import WidgetRegistry
from src.ui.widgets.widgets import custom_input_box
from src.ui.widgets.config import DEFAULT_WIDGETS

from src.utils import file_log
from collections import defaultdict


def set_defaults():
    """set session state variables defaults"""
    if "initialised" in st.session_state:
        return
    default_parameters = {
        "user": None,
        "supabase_client": init_connection(),
        "expired_tokens": None,
        "supabase_tokens": None,
        "did_try_restore": False,
        "cookies_worked": False,
        "tokens_to_save": None,
        "active_problem_types": [],
        "game_score": 0,
        "game_end_time": 0,
        "is_game_running": False,
        "fade_class_identifier": 0,
        "game_mode_selection": None,
        "problem_id": 0,
        "problem_types_segmented_control": [0],
        "GameTelemetry": None,
        "symbols": {
            "add": r"$+$",
            "subtract": r"$-$",
            "mult": r"$\times$",
            "div": r"$\div$",
        },
        "callables": {
            "streamlit":{
                "checkbox": st.checkbox,
                "slider": st.slider,
                "number_input_box": st.number_input,
                "segmented_control": st.segmented_control,
                "text_input_boxes": st.text_input,
                "buttons": st.button,
                },
            "custom": {
                "number_input_box": custom_input_box
            }
        },
        "problem_type_index_map": {
            0: {"operation": "add", "dtype": "ints"},
            1: {"operation": "subtract", "dtype": "ints"},
            2: {"operation": "mult", "dtype": "ints"},
            3: {"operation": "div", "dtype": "ints"},
            },
        }

    for parameter, default in default_parameters.items():
        st.session_state.setdefault(parameter, default)

    set_default_config()

    return

def set_default_config(suppress=True):
    if "suppress" not in st.session_state:
        st.session_state["suppress"] = suppress
    if "config" in st.session_state:
        #print("default config already set.")
        return

    file_log("session state has no config, initialising config")
    def tree():
        return defaultdict(tree)

    config = tree()
    st.session_state["config"] = config

    for widget_category, widgets in DEFAULT_WIDGETS.items():
        for widget_name, widget_config in widgets.items():

            WidgetRegistry.register(
                widget_name= widget_name,
                widget_category=widget_category,
                **widget_config
            )

    if not st.session_state["suppress"]:
        print("Initialisation complete. To suppresses these startup messages, call set_default_config(suppress=True) in `config_management.py` instead.")

    st.session_state["initialised"] = True
    print("default session state and widget configurations initialised")