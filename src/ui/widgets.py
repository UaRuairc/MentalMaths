import streamlit as st
import streamlit.components.v1 as components
import os

custom_input = components.declare_component(
    "custom_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)

slider_descriptions = {
    "add": "Choose range for addition",
    "subtract": "Choose range for subtraction",
    "mult": "Choose range for multiplication",
    "div": "Choose range for division",
}


META_ARGS = {
    "widget_category",
    "extra_callback"
}

class MakeWidget():
    """how widgets seem to work in streamlit:

    Widgets are identified by a key:value pair in session_state, where the value is, for example, the range on a slider:
    session_state["my_widgets_key"] = value it is currently set to

    However:

    1. To update the app state, streamlit uses st.rerun().
    2. When st.rerun() is called, if streamlits doesnt render your widget again on that run, it makes the
    widget stateless and you lose your stored info about the widget

    See: https://docs.streamlit.io/develop/concepts/multipage-apps/widgets for solutions to this.

    We opt for a widget wrapper that takes a configuration

    1. This makes it less painful to switch UI frameworks if necessary.
    2. Once the config is made, you only ever have to type MakeWidget(),
    you don't have to go through the whole rigmarole of making sure your widget always has the right
    value .

    """
    def __init__(self, widget_config_key, widget_category, **kwargs):
        self.widget_config_key, self.widget_category = widget_config_key, widget_category
        self.widget_config = st.session_state["config"][self.widget_category][self.widget_config_key].copy()
        self.widget_config.update(kwargs)
        self.widget_state_key = self.widget_config["key"]
        self.previous_widget_value = self.widget_config["value"]
        self.widget_config["on_change"] = self._on_change
        self.callable = st.session_state["callables"][self.widget_category]
        self.extra_on_change = self.widget_config.get("extra_callback", None)



    def ensure_initialisation(self):
        st.session_state[self.widget_state_key] = self.previous_widget_value

    def _on_change(self):
        # here we update the CONFIGURATION we use to build future sliders of this type
        updated_value = st.session_state[self.widget_state_key]
        st.session_state["config"][self.widget_category][self.widget_config_key]["value"] = updated_value

        if self.extra_on_change:
            self.extra_on_change()

    def render(self):
        self.ensure_initialisation()
        render_config = self.clean_widget_config()
        self.callable(**render_config)

    def clean_widget_config(self):

        """
         Unfortunately, even though we update the session state, in the event one does not pass a value,
         when first building a slider streamlit tells the frontend to build a slider with:

         value=(min,max)

         for a fraction of a section, before setting:

         value=session_state[key]

         this results in a flicker, so we have to pass value if we plan to hide/show sliders
         """

        render_config = self.widget_config.copy()

        render_config.pop("default", None)
        if render_config["widget_category"] == "segmented_control":
            render_config["default"] = render_config["value"]

        if render_config["widget_category"] != "sliders":
            render_config.pop("value", None)

        for arg in META_ARGS:
            render_config.pop(arg, None)

        if "disabled" in render_config and callable(render_config["disabled"]):
            render_config["disabled"] = render_config["disabled"]()

        return render_config


    @staticmethod
    def current_value(widget_category, widget_config_key):
        return st.session_state["config"][widget_category][widget_config_key]["value"]

class LeftRightSliders():

    def __init__(self, problem_type):
        self.problem_type = problem_type
        self.cols = None
        self.left_config_key = f"{self.problem_type}_left"
        self.right_config_key = f"{self.problem_type}_right"
        self.left_slider = MakeWidget(self.left_config_key, "sliders")
        self.right_slider = MakeWidget(self.right_config_key, "sliders")

    def render(self):
        self.make_columns()
        with self.cols[0]:
            st.write(slider_descriptions[self.problem_type[:-5]])
        with self.cols[1]:
            self.left_slider.render()
        with self.cols[2]:
            self.right_slider.render()

    def make_columns(self):
        self.cols = st.columns(3)

    @staticmethod
    def range(type_):
        left_range = st.session_state["config"]["sliders"][f"{type_}_left"]["value"]
        right_range = st.session_state["config"]["sliders"][f"{type_}_right"]["value"]
        return [left_range, right_range]

def custom_input_box(problem_id_, correct_answer, key_, alignment_="center"):
    result = custom_input(
        key=key_,
        correctAnswer=str(correct_answer),
        alignment=alignment_,
        problemId=problem_id_,
    )
    if result is None:
        return ""
    return result