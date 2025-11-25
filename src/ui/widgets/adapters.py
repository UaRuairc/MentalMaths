import streamlit as st
import abc
from src.ui.widgets.registry import WidgetRegistry

class WidgetAdapter(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def render_params(cls, name, category):
        pass

    @classmethod
    @abc.abstractmethod
    def _sync(cls, widget_config):
        pass

    @classmethod
    @abc.abstractmethod
    def initialise(cls, name, category):
        pass

    @classmethod
    @abc.abstractmethod
    def wrap_on_change(cls, widget_config):
        pass

    @classmethod
    @abc.abstractmethod
    def render(cls, name, category, **kwargs):
        pass

class StreamlitWidgetAdapter(WidgetAdapter):
    @classmethod
    def render_params(cls, name, category):
        widget_config = st.session_state["config"][category][name]
        render_config = widget_config.framework_params

        for key, value in render_config.items():
            if key not in ["on_change", "format_func"] and callable(value):
                render_config[key] = value()
            elif key == "on_change":
                render_config[key] = cls.wrap_on_change(widget_config=widget_config)

        return render_config

    @classmethod
    def _sync(cls, widget_config):
        widget_config.set(st.session_state[widget_config["key"]])

    @classmethod
    def initialise(cls, name, category):
        if not (category in st.session_state["config"] and name in st.session_state["config"][
            category]):
            raise RuntimeError(
                f"Widget not registered: Register [{category}:{name}] before creating the widget instance")

        widget_config = st.session_state["config"][category][name]
        st.session_state[widget_config["key"]] = widget_config._params["value"]

    @classmethod
    def wrap_on_change(cls, widget_config):
        if "on_change" in widget_config.framework_params:
            def on_change():
                cls._sync(widget_config)
                extra_callback = widget_config.get("extra_callback", None)
                if extra_callback:
                    extra_callback()

            return on_change
        return None


    @classmethod
    def render(cls, name, category, **kwargs):
        renderer = st.session_state["callables"]["streamlit"][category]
        value = renderer(**(cls.render_params(name, category) | kwargs))
        return value


class CustomWidgetAdapter(StreamlitWidgetAdapter):


    @classmethod
    def initialise(cls, name, category):
        if not (category in st.session_state["config"] and name in st.session_state["config"][
            category]):
            raise RuntimeError(
                f"Widget not registered: Register [{category}:{name}] before creating the widget instance")

    @classmethod
    def render(cls, name, category, **kwargs):
        renderer = st.session_state["callables"]["custom"][category]
        value = renderer(**(cls.render_params(name, category) | kwargs))
        return value



WIDGET_ADAPTERS = {
    "streamlit": StreamlitWidgetAdapter,
    "custom": CustomWidgetAdapter,
}