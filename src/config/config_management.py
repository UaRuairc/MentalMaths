import streamlit as st
import inspect
from src.ui.widgets import custom_input_box, MakeWidget

class ConfigManager:

    @staticmethod
    def generate_config(name: str, widget_category: str, **overrides):
        if "callables" not in st.session_state:
            st.session_state["callables"] = {
                "checkboxes": st.checkbox,
                "sliders": st.slider,
                "number_input_boxes": st.number_input,
                "custom_input_boxes": custom_input_box,
                "segmented_control": st.segmented_control
            }

        #Generate config for any widget type using introspection
        widget_callable = st.session_state["callables"][widget_category]
        sig = inspect.signature(widget_callable)
        config = {}

        for param_name, param in sig.parameters.items():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            if param.default is not inspect.Parameter.empty:
                config[param_name] = param.default
                continue

            # doesn't have a default, needs to be set, assume user provides overrides.
            config[param_name] = None


        # This is a bit hacky, functional, but improve later...
        config["widget_category"] = widget_category
        config["name"] = name
        if widget_category[-5:] == "boxes":
            config["key"] = f"{name}_{widget_category[:-2]}"
        elif widget_category == "sliders":
            config["key"] = f"{name}_{widget_category[:-1]}"
        else:
            config["key"] = f"{name}_{widget_category}"

        config["label"] = f"{name}"
        config["on_change"] = None

        if widget_category == "number_input_boxes":
            config["value"] = 0

        # some streamlit widgets do not have a `value` parameter
        #
        # MakeWidget generically uses the value param to store info on how to rebuild the widget, whether the widget has
        # a `value` parameter or not. MakeWidget then updates the config so "value" is renamed to whatever key that widget uses
        if "value" not in config:
            config["value"] = None
        # Apply overrides
        for param in overrides:
            config[param] = overrides[param]

        return config

    @staticmethod
    def add_to_session_state(config):
        config_copy = config.copy()

        name = config["name"]
        config_copy.pop("name")

        category = config["widget_category"]
        st.session_state["config"][category][name] = config_copy
        if st.session_state["suppress"] == False:
            print("\n Added config to session state: {}\n".format(st.session_state["config"][category][name] ))

    @staticmethod
    def validate_config(widget_key, widget_category):
        MakeWidget(widget_key, widget_category)
        # work in progress

    @staticmethod
    def add_widget(name: str, widget_category: str, **overrides):
        if name in st.session_state["config"][widget_category]:
            # print(f"A {widget_category} widget with this name already exists. Choose a different name.")
            return

        config = ConfigManager.generate_config(name, widget_category, **overrides)

        ConfigManager.add_to_session_state(config)


    @staticmethod
    def remove_widget(name: str, widget_category: str):
        st.session_state["config"][widget_category].pop(name)

    @staticmethod
    def get_widget_value(widget_name, widget_category):
        return st.session_state["config"][widget_category][widget_name]["value"]