import streamlit as st
import streamlit.components.v1 as components
import os

custom_input = components.declare_component(
    "fast_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)


class Slider():
    """ How widgets seem to work in streamlit

    Widgets are identified by a key:value pair in session_state, where the value is for example the range on a slider
    session_state["my_widgets_key"] = value

    However: streamlit functions by rerunning the app, and even if you made a widget earlier, if this run does not
    render the widget, streamlit deletes the info associated with it

    See: https://docs.streamlit.io/develop/concepts/multipage-apps/widgets for solutions to this

    One option is to just write

    def store_value(key):
        st.session_state[key] = st.session_state["_"+key]
    def load_value(key):
        st.session_state["_"+key] = st.session_state[key]

    for each key. BUT then you are restricted, because the key doesn't store the ENTIRE configuration.

    We opt for a shadow copy for more freedom down the line.

    """

    # The streamlit session state is essentially just a dictionary.
    # So, "storing a widget" in the session_state really means:
    # -- "Storing the config settings so we can render the widget whenever/wherever we need
    # the config contains the values of the widget AND its key, which is its unique identifier.

    # So, if you have the config, you can just call widget(**config) whenever you want
    # This class is just a wrapper for a slider widget that CAN render the widget if required.

    def __init__(self, config_key):
        self.config_key = config_key
        self.config = st.session_state[self.config_key]

        self.slider_key = self.config["key"]
        self.slider_value_range = self.config["value"]

        self.config["on_change"] = self._on_change

        # now we make sure the slider knows, next time you render, you should have the current config value
        st.session_state[self.slider_key] = self.slider_value_range

    def _on_change(self):
        # here we update the CONFIGURATION used to build future sliders of this type
        value = st.session_state[self.slider_key]
        st.session_state[self.config_key]["value"] = value

    def render_slider(self):
        st.slider(**self.config)

    def range(self):
        return st.session_state[self.config_key]["value"]

class LeftRightSliders():

    def __init__(self, problem_type):
        self.cols = st.columns(3)
        self.problem_type = problem_type
        self.left_config_key = f"{self.problem_type}_left_slider_config"
        self.right_config_key = f"{self.problem_type}_right_slider_config"
        self.left_slider = Slider(self.left_config_key)
        self.right_slider = Slider(self.right_config_key)

    def render(self):
        with self.cols[0]:
            st.write(f"range for {self.problem_type}")
        with self.cols[1]:
            self.left_slider.render_slider()
        with self.cols[2]:
            self.right_slider.render_slider()

    def range(self):
        return [self.left_slider.range(), self.right_slider.range()]

# depreciated
def draw_checkbox(problem_type_key):
    val = st.checkbox(problem_type_key, value=st.session_state[problem_type_key])
    st.session_state[problem_type_key] = val

class Checkbox:
    def __init__(self, problem_type):
        self.problem_type = problem_type
        self.config = dict(st.session_state[f"{self.problem_type}_checkbox_config"])
        self.config["on_change"] = self._on_change
        # self.config.pop("value", None)

        if f"{self.problem_type}_checkbox" not in st.session_state:
            st.session_state[f"{self.problem_type}_checkbox"] = self.config["value"]

    def _on_change(self):
        st.session_state[f"{self.problem_type}_checkbox_config"]["value"] = st.session_state[
            self.config["key"]]

    def render_checkbox(self):
        self.config.pop("value", None)
        st.checkbox(**self.config)

def custom_input_box():
    result = custom_input(
        key="constant_custom_input_key",
        correctAnswer=str(st.session_state["current_problem"].answer), # correctAnswer is used by CustomInput.tsx to determine if the input field needs resetting.
        height=80,
        width=200,
    )
    if result is None:
        return ""
    return result
