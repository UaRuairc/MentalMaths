import streamlit as st
from src.game.content.problem_engine import Question
from src.config.config_management import ConfigManager as cm
from src.game.gameplay.game_controller import start_game
from src.ui.widgets import MakeWidget
from src.utils import inject_centring_css, get_range

checkbox_keys = ["add_ints_checkbox", "subtract_ints_checkbox", "mult_ints_checkbox",
                 "div_ints_checkbox"]
default_style = ("text-align: center; font-size: 3rem; font-weight: bold; width: 80px; margin: 0 auto; "
                 "display: flex; align-items: center; justify-content: center; min-height: 80px;")
# currently dynamically make some widget configurations on this page at runtime, so defaults not in config yet, initialise here



def display_settings(settings_containers):
    render_base_settings(settings_containers)
    render_modifier_settings(settings_containers)
    update_active_problem_types()
    render_active_problem_type_settings(settings_containers)

def render_base_settings(settings_containers):
    with settings_containers["base_settings"]:

        base_settings_cols = st.columns(3, vertical_alignment="center")

        base_ui_positioning = {
            "segmented_control": {
                "problem_types": base_settings_cols[0],
                "duration": base_settings_cols[1],
            },
            "number_input_box": {
                "duration": base_settings_cols[2],
            }

        }

        build_ui_from_map(positioning_map=base_ui_positioning)

def render_modifier_settings(settings_containers):

    """

    create checkbox wrappers and render them. The wrapper updates their state, i.e. ticked/not ticked.

    """

    with settings_containers["modifier_settings"]:
        st.write("Game Modifiers")
        modifier_settings_cols = st.columns(1, vertical_alignment="center")

        if not cm.is_registered(widget_name="enable_db", widget_category="checkbox"):
            cm.register(
                widget_name="enable_db",
                widget_category="checkbox",
                **{"value": True},
            )

        modifier_ui_positioning = {
            "checkbox": {
                "pos_answers_only": modifier_settings_cols[0],
                "fade_problem": modifier_settings_cols[0],
                "enable_db": modifier_settings_cols[0]
            }
        }

        build_ui_from_map(positioning_map=modifier_ui_positioning)

def update_active_problem_types():
    """

    example: if the integer addition and integer division options are ticked, then we update the session state:
    st.session_state["active_problem_types"] = (("add", "ints""), ("div", "ints"))

    """
    index_map = st.session_state["problem_type_index_map"]
    selections = sorted(cm.get_value("problem_types", "segmented_control"))
    st.session_state["active_problem_types"] = [
        (index_map[index_]["operation"], index_map[index_]["dtype"])
        for index_ in selections
    ]
    #print(st.session_state["config"]["segmented_control"]["problem_types"]["value"])
    #print(st.session_state["active_problem_types"])

def render_active_problem_type_settings(settings_containers):
    """

    for all active problem type, render input boxes for user to choose the range of problems generated

    """
    with settings_containers["range_settings"]:
        for op, type in st.session_state["active_problem_types"]:
            render_range_inputs(f"{op}_{type}",  symbol=st.session_state["symbols"][op])

def render_range_inputs(type_, symbol="+"):

    """

    For a given active problem type, render a row of input boxes

    Each row is displayed as:

    [? -> ?] + [? -> ?]  = [? -> ?]

    We will render all the boxes, but disable the boxes that contain the answer range. That way the user can know the
    range of problems that they can expect.

    For division problems, we disable the FIRST box, i.e., the dividend

    """

    range_display_cols = st.columns([1, 8, 1, 8, 1, 8, 1], vertical_alignment="center")
    inject_centring_css()

    if type_ != "div_ints":
        disabled_box = "c"
    else:
        disabled_box = "a"


    keys = (
        f"{type_}_a_min", f"{type_}_a_max", f"{type_}_b_min", f"{type_}_b_max", f"{type_}_c_min", f"{type_}_c_max"
    )

    def update_disabled_boxes_on_change(type_, disabled_box):
        def wrapper():
            #print(type_, disabled_box)
            min_, max_ = Question.calc_theoretical_range(
                type_=type_[:-5],
                ranges_=lambda: get_range(type_),
                pos_answers_only= lambda: cm.get_value("pos_answers_only", "checkbox"))

            cm.set_value(f"{type_}_{disabled_box}_min", "number_input_box", min_)
            cm.set_value(f"{type_}_{disabled_box}_max", "number_input_box", max_)

        return wrapper

    if not cm.is_registered(widget_name=keys[0], widget_category="number_input_box"):
        # the widgets need to be added to the config
        # add the ones that are not disabled first, then the disabled one last

        # we need to give them some initial values
        initial_range = {
            "add_ints": [(3, 100), (3, 100)],
            "subtract_ints": [(3, 100), (3, 100)],
            "mult_ints": [(3, 12), (3, 12)],
            "div_ints": [(3, 12), (3, 12)],
        }

        if disabled_box == "c":
            a_min, a_max, b_min, b_max = sum(initial_range[type_], ())
            c_min, c_max = Question.calc_theoretical_range(
                type_=type_[:-5],
                ranges_=( (a_min, a_max), (b_min, b_max) ),
                pos_answers_only=cm.get_value("pos_answers_only", "checkbox")
            )


            active = [
                (a_min, f"{type_}_a_min"),
                (a_max, f"{type_}_a_max"),
                (b_min, f"{type_}_b_min"),
                (b_max, f"{type_}_b_max"),
                      ]
            disabled = [
                (c_min, f"{type_}_c_min"),
                (c_max, f"{type_}_c_max"),
            ]

        else:
            b_min, b_max, c_min, c_max = sum(initial_range[type_], ())
            a_min, a_max = Question.calc_theoretical_range(
                type_=type_[:-5],
                ranges_=( (b_min, b_max), (c_min, c_max) ),
                pos_answers_only=cm.get_value("pos_answers_only", "checkbox")
            )

            active = [
                (b_min, f"{type_}_b_min"),
                (b_max, f"{type_}_b_max"),
                (c_min, f"{type_}_c_min"),
                (c_max, f"{type_}_c_max"),
            ]
            disabled = [
                (a_min, f"{type_}_a_min"),
                (a_max, f"{type_}_a_max"),
            ]

        for val, widget_name in active:

            cm.register(
                widget_name=widget_name,
                widget_category="number_input_box",
                **{"step": 1, "label_visibility": "collapsed", "value": val, "disabled": False},
                extra_callback=update_disabled_boxes_on_change(type_, disabled_box)
            )

        for val, widget_name in disabled:

            cm.register(
                widget_name=widget_name,
                widget_category="number_input_box",
                **{"step": 1, "label_visibility": "collapsed", "value": val, "disabled": True},
            )

    with range_display_cols[1]:
        make_number_boxes(type_=type_, position_ = "a")

    with range_display_cols[2]:
        st.markdown(symbol)

    with range_display_cols[3]:
        make_number_boxes(type_=type_, position_ = "b")

    with range_display_cols[4]:
        st.markdown("=")

    with range_display_cols[5]:
        make_number_boxes(type_=type_, position_="c")

    if type_ == "subtract_ints":
        if cm.get_value(
                widget_name="pos_answers_only",
                widget_category="checkbox",
                arg="extra_callback") is None:
            #need a callback to update the answer range when the pos_answers_only checkbox is toggled
            cm.set_value(widget_name="pos_answers_only", widget_category="checkbox",
                         arg="extra_callback",
                         updated_arg_value=update_disabled_boxes_on_change(type_="subtract_ints", disabled_box ="c"))


def make_number_boxes(type_, position_):
    get_val = lambda key_: cm.get_value(widget_name=key_, widget_category="number_input_box")
    flip = {"min": "max", "max": "min"}
    render_box = lambda kind_: MakeWidget(
                                    widget_config_key=f"{type_}_{position_}_{kind_}",
                                    widget_category="number_input_box",
                                    **{flip[kind_] + "_value": get_val(f"{type_}_{position_}_" + flip[kind_])},
    ).render()


    with st.container(border=True):
        placements3 = st.columns([5, 2, 5], vertical_alignment="center")
        with placements3[0]:
            render_box("min")
        with placements3[1]:
            st.markdown(":material/arrow_right_alt:")
        with placements3[2]:
            render_box("max")

def is_start_button_disabled():

    current_duration_value = cm.get_value("duration", "number_input_box")
    current_duration_option = cm.get_value("duration", "segmented_control")

    no_types_selected = not st.session_state["active_problem_types"]
    duration_not_set = (
            current_duration_option is None or
            current_duration_value is None or
            current_duration_value <= 0
    )
    disable_start_button_condition = no_types_selected or duration_not_set

    help_message = (
        "Please select at least one problem type and set a duration to begin the game" if no_types_selected and duration_not_set else
        "Please select at least one problem type to begin the game" if no_types_selected else
        "Please set a duration to begin the game" if duration_not_set else
        None
    )

    return disable_start_button_condition, help_message

def display_start_button_and_help_messages(settings_containers):

    disable_start_button_condition, help_message = is_start_button_disabled()

    with settings_containers["start_button"]:
        col1, col2 = st.columns([1, 4], vertical_alignment="center")
        with col1:
            if st.button("start_game", disabled=disable_start_button_condition, help=help_message):
                start_game()
        with col2:
            if help_message:
                st.info(help_message)

def build_ui_from_map(positioning_map):
    for widget_category, widget_column_pairs in positioning_map.items():
        for key, column in widget_column_pairs.items():
            with column:
                MakeWidget(widget_config_key=key, widget_category=widget_category).render()