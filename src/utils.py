import streamlit as st
import logging
import json
import threading
from streamlit.runtime.scriptrunner import get_script_run_ctx
import inspect
import time

default_style = "text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center; min-height: 80px;"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    filename="debug.log",   # name of your log file
    filemode="a"            # append mode
)

def log_game_state(label: str):
    """get current session_state variables and log them"""
    snapshot = {}
    for key, value in st.session_state.items():
        try:
            json.dumps(value)
            snapshot[key] = value
        except TypeError:
            # some objects not serializable.
            snapshot[key] = repr(value)

    logging.info(f"{label}: {json.dumps(snapshot)}")

def guard():
    """A guard function that should never be needed. But logging if it ever is necessary for future debugging"""
    if not st.session_state["active_problem_types"]:
        log_game_state("guard() was triggered")
        st.session_state["is_game_running"] = False
        return

def debug_fragment_info(label=""):
    """
    Print comprehensive debug information about the current fragment execution.

    Usage:
        @st.fragment(run_every=0.5)
        def my_timer():
            debug_fragment_info("Timer")
            # ... rest of your code
    """
    # Get context
    ctx = get_script_run_ctx()

    # Timestamp and execution tracking
    timestamp = time.time()
    if "debug_execution_count" not in st.session_state:
        st.session_state["debug_execution_count"] = 0
    st.session_state["debug_execution_count"] += 1

    # Collect all debug info
    debug_info = {
        "label": label,
        "execution_number": st.session_state["debug_execution_count"],
        "timestamp": f"{timestamp:.4f}",
        "thread_id": threading.current_thread().ident,
        "thread_name": threading.current_thread().name,
    }

    # Context info
    if ctx:
        debug_info.update({
            "fragment_id": ctx.current_fragment_id,
            "session_id": ctx.session_id[-8:] if ctx.session_id else "None",
            "script_run_id": getattr(ctx, 'script_run_id', 'N/A'),
            "page_script_hash": getattr(ctx, 'page_script_hash', 'N/A')[:8] if hasattr(ctx,
                                                                                       'page_script_hash') else 'N/A',
        })

        # Try to get fragment-specific info
        if hasattr(ctx, 'fragment_id'):
            debug_info["fragment_id"] = ctx.fragment_id
        elif hasattr(ctx, 'dg_stack') and ctx.dg_stack:
            debug_info["dg_stack_depth"] = len(ctx.dg_stack)

    # Caller info
    caller_frame = inspect.currentframe().f_back
    debug_info["caller_function"] = caller_frame.f_code.co_name
    debug_info["caller_line"] = caller_frame.f_lineno

    # Check for rapid executions
    if "last_fragment_time" in st.session_state:
        time_since_last = timestamp - st.session_state["last_fragment_time"]
        debug_info["time_since_last"] = f"{time_since_last:.3f}s"
        if time_since_last < 0.1:
            debug_info["WARNING"] = "RAPID EXECUTION (<0.1s)"
    st.session_state["last_fragment_time"] = timestamp

    # Format output
    output = f"\n{'=' * 60}\n"
    output += f"FRAGMENT DEBUG: {label}\n"
    output += f"{'-' * 60}\n"

    for key, value in debug_info.items():
        output += f"{key:<20}: {value}\n"

    output += f"{'=' * 60}\n"

    print(output)

    # Return the info dict for programmatic use
    return debug_info


def track_reruns(location=""):
    """
    Track script reruns with location info.

    Usage:
        track_reruns("start of app.py")
        track_reruns("after answer validation")
    """
    if "rerun_count" not in st.session_state:
        st.session_state["rerun_count"] = 0
        st.session_state["rerun_times"] = []

    st.session_state["rerun_count"] += 1
    current_time = time.time()

    # Track time between reruns
    time_since_last = None
    if st.session_state["rerun_times"]:
        time_since_last = current_time - st.session_state["rerun_times"][-1]

    st.session_state["rerun_times"].append(current_time)

    # Keep only last 10 rerun times
    if len(st.session_state["rerun_times"]) > 10:
        st.session_state["rerun_times"] = st.session_state["rerun_times"][-10:]

    output = f"\n{'*' * 40}\n"
    output += f"RERUN #{st.session_state['rerun_count']} at {location}\n"
    output += f"Time: {time.strftime('%H:%M:%S', time.localtime(current_time))}\n"

    if time_since_last is not None:
        output += f"Time since last rerun: {time_since_last:.3f}s\n"
        if time_since_last < 0.1:
            output += "WARNING: Very rapid rerun!\n"

    output += f"{'*' * 40}\n"

    print(output)

def inject_fade_css(unique_class):
    st.markdown(f"""
            <style>
            @keyframes fadeAnimation{st.session_state["fade_class_identifier"]} {{
                from {{ opacity: 1; }}
                to {{ opacity: 0; }}
            }}
            .{unique_class} {{
                animation: fadeAnimation{st.session_state["fade_class_identifier"]} 1s ease-in-out forwards;
                animation-delay: 1s;
            }}
            </style>
            """, unsafe_allow_html=True)

def get_fade_html(unique_class, base_style=default_style):
    return f"<div class='{unique_class}' style='{base_style}'>"