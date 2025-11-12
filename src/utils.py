import streamlit as st
import logging, json, threading, inspect, time, gzip, hashlib, functools
from streamlit.runtime.scriptrunner import get_script_run_ctx
from collections import defaultdict
from contextlib import contextmanager
from src.config.config_management import WidgetRegistry
from datetime import datetime
from uuid import UUID
default_style = "text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center; min-height: 80px;"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(message)s",
    datefmt="%H:%M:%S",
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

def get_fade_html(unique_class, base_style=default_style):
    return f"<div class='{unique_class}' style='{base_style}'>"

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

def inject_centring_css():
    st.markdown(
        """
        <style>
        /* Center all markdown content */
        [data-testid="stMarkdown"]{
            display:flex;
            align-items:center;
            justify-content:center;
            height:100%;
            width:100%;
            margin:0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Module‑level globals (not in session_state)
_debug_counter = 0
_last_rerun   = None

def file_log(msg: str):
    """Append a timestamped message to your debug.log without touching session_state."""
    logging.info(f"{msg}")

def debug_fragment_to_file(label=""):
    """Write detailed fragment/debug info to debug.log (no session_state mutation)."""
    global _debug_counter
    _debug_counter += 1
    now = time.time()
    ctx = get_script_run_ctx()
    lines = [
        "\n" + "="*40,
        f"DEBUG #{_debug_counter}: {label}",
        "-"*40,
        f"timestamp        : {now:.4f}",
        f"thread           : {threading.current_thread().name}",
    ]
    if ctx:
        lines.append(f"session_id (last8): {ctx.session_id[-8:]}")
        lines.append(f"fragment_id       : {getattr(ctx, 'fragment_id', 'N/A')}")
    caller = inspect.currentframe().f_back
    lines.append(f"caller            : {caller.f_code.co_name}@{caller.f_lineno}")
    lines.append("="*40 + "\n")
    logging.info("\n".join(lines))

def track_rerun_to_file(location=""):
    """Log each script rerun to debug.log with timing, no session_state."""
    global _last_rerun
    now = time.time()
    lines = [
        "\n" + "*"*40,
        f"RERUN at {location}",
        f"time       : {time.strftime('%H:%M:%S', time.localtime(now))}"
    ]
    if _last_rerun is not None:
        delta = now - _last_rerun
        lines.append(f"since last : {delta:.3f}s")
        if delta < 0.1:
            lines.append("**WARNING: rapid rerun**")
    lines.append("*"*40 + "\n")
    logging.info("\n".join(lines))
    _last_rerun = now

def get_range(next_problem_tag):
    get_val = lambda name: WidgetRegistry.get_widget_value(widget_name=name, widget_category="number_input_box")

    if next_problem_tag != "div_ints":
        #(l1, r1) + (l2, r2) = ?
        l1 = get_val(f"{next_problem_tag}_a_min")
        r1 = get_val(f"{next_problem_tag}_a_max")
        l2 = get_val(f"{next_problem_tag}_b_min")
        r2 = get_val(f"{next_problem_tag}_b_max")
    else:
        # (l1, r1) + (l2, r2) = ...
        l1 = get_val(f"{next_problem_tag}_b_min")
        r1 = get_val(f"{next_problem_tag}_b_max")
        l2 = get_val(f"{next_problem_tag}_c_min")
        r2 = get_val(f"{next_problem_tag}_c_max")
    range1 = (l1, r1)
    range2 = (l2, r2)

    return range1, range2

def get_ranges():
    """
    May use different widgets at different times to collect info
    for example: we might use sliders in the future, or stick with input boxes.
    This helper is where we make sure we collect the data from the right place
    atm just collects from v0.2 UI
    """

    ranges = {}

    for op, dtype in st.session_state["active_problem_types"]:
        r = get_range(f"{op}_{dtype}")

        if f"{op}_{dtype}" != "div_ints":
            ranges[f"{op}_{dtype}"] = {
                "left_operand_range": r[0],
                "right_operand_range": r[1],
            }
        else:
            ranges[f"{op}_{dtype}"] = {
                "divisor_range": r[0],
                "quotient_range": r[1],
            }
    return ranges


def to_plain(o):
    if isinstance(o, defaultdict):
        o = dict(o)
    if isinstance(o, dict):
        return {k: to_plain(v) for k, v in o.items()}
    if isinstance(o, list):
        return [to_plain(v) for v in o]
    return o

def config_stats(cfg):
    plain = to_plain(cfg)
    def extract_values(d):
        out = {}
        for g, group in (d or {}).items():
            if isinstance(group, dict):
                out[g] = {k: (v.get("value") if isinstance(v, dict) and "value" in v else v)
                          for k, v in group.items()}
            else:
                out[g] = group
        return out

    normalized = extract_values(plain)

    s = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    raw = s.encode("utf-8")
    gz = gzip.compress(raw)
    return {
        "json_bytes": len(raw),
        "json_kib": len(raw) / 1024,
        "gzip_bytes": len(gz),
        "gzip_kib": len(gz) / 1024,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "normalized": normalized,  # remove if you don't want to print the whole thing
    }

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.4f}s")
        return result

    return wrapper

@contextmanager
def timed_block(name="Block"):
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        print(f"{name} took {end - start:.4f}s")

def make_json_safe(data):
    if isinstance(data, dict):
        return {k: make_json_safe(v) for k, v in data.items()}
    elif isinstance(data, set):
        return list(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, UUID):
        return str(data)
    else:
        return data
