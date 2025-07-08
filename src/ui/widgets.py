import streamlit as st
import streamlit.components.v1 as components
import os

custom_input = components.declare_component(
    "fast_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)


class Slider():
    """how widgets seem to work in streamlit:

    Widgets are identified by a key:value pair in session_state, where the value is for example the range on a slider
    e.g. session_state["my_widgets_key"] = value

    However: streamlit functions by rerunning the app, and even if you made a widget earlier, if this run does not
    render the widget, streamlit deletes the info associated with it

    See: https://docs.streamlit.io/develop/concepts/multipage-apps/widgets for solutions to this.

    One option is to just write:

    def store_value(key):
        st.session_state[key] = st.session_state["_"+key]
    def load_value(key):
        st.session_state["_"+key] = st.session_state[key]

    For each key. BUT then you are restricted, because the key doesn't store the entire configuration only the value

    We opt for a shadow copy for more freedom down the line.

    """
    def __init__(self, config_key):
        self.config_key = config_key
        self.config = st.session_state["config"]["sliders"][self.config_key].copy()

        self.slider_key = self.config["key"]
        self.slider_value_range = self.config["value"]
        #print(self.slider_value_range)

        self.config["on_change"] = self._on_change

        # now we make sure the slider knows, next time you render, you should have the current config value

        st.session_state[self.slider_key] = self.slider_value_range

    def _on_change(self):
        # here we update the CONFIGURATION we use to build future sliders of this type
        value = st.session_state[self.slider_key]
        st.session_state["config"]["sliders"][self.config_key]["value"] = value

    def render_slider(self):
        self.config.pop("value")
        st.slider(**self.config)

    @staticmethod
    def range(slider_key_):
        return st.session_state["config"]["sliders"][slider_key_]["value"]

class LeftRightSliders():

    def __init__(self, problem_type):
        self.cols = st.columns(3)
        self.problem_type = problem_type

        self.left_config_key = f"{self.problem_type}_left_slider"
        self.right_config_key = f"{self.problem_type}_right_slider"

        self.left_slider = Slider(self.left_config_key)
        self.right_slider = Slider(self.right_config_key)

    def render(self):
        with self.cols[0]:
            st.write(f"range for {self.problem_type}")
        with self.cols[1]:
            self.left_slider.render_slider()
        with self.cols[2]:
            self.right_slider.render_slider()

    @staticmethod
    def range(type_):
        left_range = st.session_state["config"]["sliders"][f"{type_}_left_slider"]["value"]
        right_range = st.session_state["config"]["sliders"][f"{type_}_right_slider"]["value"]
        return [left_range, right_range]

class Checkbox:
    def __init__(self, problem_type):
        self.problem_type = problem_type
        self.config_key = f"{self.problem_type}_checkbox"
        self.config =  st.session_state["config"]["checkboxes"][self.config_key].copy()

        self.box_key = self.config["key"]
        self.config["on_change"] = self._on_change

        # make sure the box starts with the config's value

        st.session_state[self.box_key] = self.config["value"]


    def _on_change(self):
        st.session_state["config"]["checkboxes"][self.config_key]["value"] = st.session_state[self.box_key]

    def render_checkbox(self):
        self.config.pop("value", None)
        st.checkbox(**self.config)

def custom_input_box(key_, alignment_="center"):
    result = custom_input(
        key=key_,
        correctAnswer=str(st.session_state["current_problem"].answer), # correctAnswer is used by CustomInput.tsx to determine if the input field needs resetting.
        alignment=alignment_,
    )
    if result is None:
        return ""
    return result