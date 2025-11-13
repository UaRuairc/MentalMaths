import streamlit as st
import abc

class WidgetAdapter(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def render_params(cls, name, category):
        pass

    @classmethod
    @abc.abstractmethod
    def sync(cls, widget_config):
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

        if widget_config.category == "slider": render_config[widget_config._framework_return_param] = widget_config._params["value"]

        if "disabled" in render_config and callable(render_config["disabled"]): render_config["disabled"] = \
        render_config["disabled"]()

        cls.wrap_on_change(widget_config=widget_config)
        return render_config

    @classmethod
    def sync(cls, widget_config):
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
        if "on_change" in widget_config:
            def on_change():
                cls.sync(widget_config)
                extra_callback = widget_config.get("extra_callback", None)
                if extra_callback:
                    extra_callback()

            widget_config["on_change"] = on_change

    @classmethod
    def render(cls, name, category, **kwargs):
        renderer = st.session_state["callables"]["streamlit"][category]
        value = renderer(**(cls.render_params(name, category) | kwargs))
        return value


class CustomWidgetAdapter(WidgetAdapter):
    @classmethod
    def render_params(cls, name, category):
        widget_config = st.session_state["config"][category][name]
        render_config = widget_config.framework_params
        cls.wrap_on_change(widget_config=widget_config)
        return render_config

    @classmethod
    def sync(cls, widget_config):
        pass

    @classmethod
    def initialise(cls, name, category):
        if not (category in st.session_state["config"] and name in st.session_state["config"][
            category]):
            raise RuntimeError(
                f"Widget not registered: Register [{category}:{name}] before creating the widget instance")

    @classmethod
    def wrap_on_change(cls, widget_config):
        if "on_change" in widget_config:
            def on_change():
                cls.sync(widget_config)
                extra_callback = widget_config.get("extra_callback", None)
                if extra_callback:
                    extra_callback()

            widget_config["on_change"] = on_change

    @classmethod
    def render(cls, name, category, **kwargs):
        renderer = st.session_state["callables"]["custom"][category]
        value = renderer(**(cls.render_params(name, category) | kwargs))
        return value



WIDGET_ADAPTERS = {
    "streamlit": StreamlitWidgetAdapter,
    "custom": CustomWidgetAdapter,
}