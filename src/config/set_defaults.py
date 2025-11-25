import streamlit as st

from src.database.connection import init_connection
from src.ui.widgets.registry import WidgetRegistry
from src.config.defaults import OPERATOR_SYMBOLS, WIDGET_CALLABLES, PROBLEM_TYPE_INDEX_MAP, DEFAULT_WIDGETS_V_02

from src.utils import file_log
from collections import defaultdict


def set_defaults():
    """Initialize session state variables and widget configurations"""
    if "initialised" in st.session_state and "registered" in st.session_state:
        return

    # Initialize supabase connection (cached via @st.cache_resource)
    st.session_state["supabase_client"] = init_connection()

    # Initialize custom widgets for WIDGET_CALLABLES if needed
    from src.config.defaults import _init_custom_widgets
    _init_custom_widgets()

    default_parameters = {
        "user": None,
        "symbols": OPERATOR_SYMBOLS,
        "callables": WIDGET_CALLABLES,
        "problem_type_index_map": PROBLEM_TYPE_INDEX_MAP,
        "expired_tokens": None,
        "supabase_tokens": None,
        "did_try_restore": False,
        "cookies_worked": False,
        "tokens_to_save": None,
        "active_problem_types": [],
        "game_score": 0,
        "is_game_running": False,
        "fade_class_identifier": 0,
        "GameTelemetry": None,
        }

    for parameter, default in default_parameters.items():
        st.session_state.setdefault(parameter, default)

    register_default_widget_configs()
    st.session_state["initialised"] = True

def register_default_widget_configs(suppress=True):
    """Register default widget configurations to session state"""
    if "registered" in st.session_state:
        return

    file_log("Registering default widgets")

    def tree():
        return defaultdict(tree)
    st.session_state["config"] = tree()

    for widget_category, widgets in DEFAULT_WIDGETS_V_02.items():
        for widget_name, widget_config in widgets.items():
            WidgetRegistry.register(
                widget_name=widget_name,
                widget_category=widget_category,
                **widget_config
            )

    if not suppress:
        print("Widget configuration initialization complete")

    st.session_state["registered"] = True

