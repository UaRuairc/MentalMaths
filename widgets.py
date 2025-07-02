import streamlit as st
import streamlit.components.v1 as components
import os

custom_input = components.declare_component(
    "fast_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)

class Sliders():

    # The streamlit session state is essentially just a dictionary.
    # So, "storing a widget" in the session_state really means:
    # -- "Storing the config settings so we can render the widget whenever/wherever we need
    # the config contains the values of the widget AND its key, which is its unique identifier.

    # So, if you have the config, you can just call widget(config=config) whenever you want
    # This class is just a wrapper for a slider widget that CAN render the widget if required.

    def __init__(self, tag):
        self.cols = st.columns(3, vertical_alignment="center")
        self.tag = tag
        # tag could be "add_ints" or something else ...

        self.left_config = dict(st.session_state[f"{self.tag}_left_slider_config"])
        self.right_config = dict(st.session_state[f"{self.tag}_right_slider_config"])

        # self.left_config is a dictionary of arguments needed to construct the left slider
        # self.right_config is similar for the right slider.
        # when constructing a slider, we don't want to pass the value as it can cause unexpected
        # value changes on rerun. So pop it and store it as a class variable

        self.left_value = self.left_config["value"]
        self.right_value = self.right_config["value"]
        self.left_config.pop("value")
        self.right_config.pop("value")

        # the following variable self.left_slider_key is the key which identifies the slider.
        # it is required so streamlit knows its simply UPDATING a slider rather than constantly building new ones ...
        # if no key is passed when building widgets, streamlit just makes new ones
        self.left_slider_key = self.left_config["key"]
        self.right_slider_key = self.right_config["key"]

        # initialise the values once, we do not want to keep overriding them.
        if self.left_slider_key not in st.session_state:
            st.session_state[self.left_slider_key] = self.left_value
        if self.right_slider_key not in st.session_state:
            st.session_state[self.right_slider_key] = self.right_value


        self.left_config["on_change"] = self._on_change
        self.right_config["on_change"] = self._on_change
        # _on_change needs the following arguments
        self.left_config["args"] = (f"{self.tag}_left_slider_config", self.left_slider_key)
        self.right_config["args"] = (f"{self.tag}_right_slider_config", self.right_slider_key)

    def render_sliders(self):
        with self.cols[0]:
            st.write(f"{self.tag} range")
        with self.cols[1]:
            st.slider(**self.left_config)
        with self.cols[2]:
            st.slider(**self.right_config)

    def _on_change(self, config_key, slider_key):
        # here we update the CONFIGURATION used to build future sliders of this type
        value = st.session_state[slider_key]
        st.session_state[config_key]["value"] = value

    def range(self):
        return[st.session_state[self.left_slider_key] , st.session_state[self.right_slider_key]]

# depreciated
def draw_checkbox(problem_type_key):
    val = st.checkbox(problem_type_key, value=st.session_state[problem_type_key])
    st.session_state[problem_type_key] = val

class Checkbox:
    def __init__(self, problem_type):
        self.problem_type = problem_type
        self.config = dict(st.session_state[f"{self.problem_type}_checkbox_config"])
        self.config["on_change"] = self._on_change

        if self.config["key"] not in st.session_state:
            st.session_state[self.config["key"]] = self.config["value"]
        self.config.pop("value", None)

    def _on_change(self):
        st.session_state[f"{self.problem_type}_checkbox_config"]["value"] = st.session_state[
            self.config["key"]]

    def render_checkbox(self):
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
