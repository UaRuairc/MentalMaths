import streamlit as st
import inspect
from dataclasses import dataclass, field, InitVar
from typing import Any, Optional, Dict
import abc
from functools import lru_cache

@lru_cache(maxsize=128)
def _get_callable_signature(fn):
    return inspect.signature(fn)

def build_framework_config(widget_category: str, framework: str= "streamlit") -> dict:
    """
    Generate the base config dict for a widget via introspection.

    Args:
        widget_category: The category of the widget. This must be an existing widget from a given library.
        framework: Framework namespace. Defaults to "streamlit", but one can add any framework as long as it has been
        added to the session_state callables dict.

    Returns:
        dict[str, Any]: The finished config dictionary
    """
    if "callables" not in st.session_state:
        raise RuntimeError("widget callables have not been initialised.")

    callables = st.session_state["callables"].get(framework)

    if callables is None:
        raise NotImplementedError(f"Framework {framework} is not supported. Currently, only streamlit is supported.")

    widget_callable = st.session_state["callables"][framework].get(widget_category)
    if widget_callable is None:
        raise NotImplementedError(
            f"widget category {widget_category} is not supported for framework {framework}.")

    sig = _get_callable_signature(widget_callable)
    framework_config = {}
    for param_name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if param.default is not inspect.Parameter.empty:
            framework_config[param_name] = param.default
            continue

        # doesn't have a default, needs to be set, assume user provides overrides.
        framework_config[param_name] = None
    # Some streamlit widgets do not have a `value` parameter
    # We generically uses the value param to store the framework return value
    if widget_category == "number_input_box" and framework == "streamlit" : framework_config["value"] = 0
    return framework_config

def build_extended_config(name: str, category: str):
    return {
        "widget_category": category,
        "name": name,
        "on_change": None,
        "extra_callback": None
    }

def get_return_param(config: dict):
    if "value" not in config:
        if "index" in config and "options" in config:
            return_param = "index"
        elif "default" in config:
            return_param = "default"
        else:
            return_param = None
    else:
        return_param = "value"
    return return_param

@dataclass
class WidgetConfig:
    name: str
    category: str
    framework: str = "streamlit"
    init_config: InitVar[Optional[Dict[str, Any]]] = None

    _params: dict = field(default_factory=dict)
    _framework_keys: set = field(default_factory=set)
    _framework_return_param: Optional["str"] = None

    def __post_init__(self, init_config = None):

        if "framework" in init_config:
            self.framework = init_config["framework"]
            init_config.pop("framework")

        base_framework_config = build_framework_config(widget_category=self.category, framework=self.framework)
        base_extended_config = build_extended_config(name=self.name, category=self.category)
        self._framework_return_param = get_return_param(config=base_framework_config)
        self._framework_keys = set(base_framework_config)

        try:
            self._params = (
                    self._params
                    | (base_framework_config or {})
                    | (base_extended_config or {})
                    | {"label": f"{self.name}"}
                    | (init_config or {})
                    | {"key": f"{self.name}_{self.category}"}
            )
        except Exception as e:
            raise RuntimeError(e)

    def update(self, params):
        if self._framework_return_param in params or "value" in params:
            raise RuntimeError(f"The parameter linked to the framework's return value can only be modified via a widget action (via set()).")
        self._params.update(params)

    def set(self, value):
        if not self._framework_return_param:
            return
        self._params["value"] = value

    def get(self, key, default=None): return self._params.get(key, default)

    @property
    def framework_params(self):
        return {key: self._params[key] for key in self._framework_keys}

    def __getitem__(self, key): return self._params[key]
    def __contains__(self, key): return key in self._params
    def __setitem__(self, key, value): self._params[key] = value

class WidgetRegistry:
    """
    Handles widget config generation and mutation.
    """
    def __init__(self, config):
        self.config = config

    @staticmethod
    def register(widget_name: str, widget_category: str, **overrides) -> bool:
        """
        Create and register a widget config to the session state.
        Args:
            widget_name: The name you would like to give the widget. The widget's internal label will be set to this value. Additionally,
            the current convention is to name the widget's key in the dictionary as {widget_name}_{widget_category}.
            widget_category: The category of the widget you would like to create. This must be from an existing library.
            **overrides: Additional overrides to overwrite any defaults.
        """
        if WidgetRegistry.is_registered(widget_name, widget_category):
            return False

        st.session_state["config"][widget_category][widget_name] = WidgetConfig(widget_name, widget_category, init_config=overrides)

        return True

    @staticmethod
    def deregister(widget_name: str, widget_category: str) -> bool:
        """
        For a given widget of category widget_category, removes the widget's config from the streamlit session state.
        """
        try:
            st.session_state["config"][widget_category].pop(widget_name)
        except KeyError:
            return False
        return True

    @staticmethod
    def is_registered(widget_name: str, widget_category: str) -> bool:
        """
        Check if a widget exists in the session state.
        Returns:
            bool: True if widget exists, False otherwise.
        Raises:
            NotImplementedError: If the widget category is not supported.
            KeyError: If there are no widgets in the specified category.
        """
        config = st.session_state.get("config")
        if not isinstance(config, dict):
            raise RuntimeError(f"The config is not present in the session state")
        try:
            return widget_name in config[widget_category]
        except KeyError:
            return False

    @staticmethod
    def get_widget_config(widget_name, widget_category) -> WidgetConfig | None:
        """
        Return the config for a given widget.
        Args:
            widget_name: The name of the widget.
            widget_category: The category of the widget. This must be an existing widget from a given library.
        """
        try:
            return st.session_state["config"][widget_category][widget_name]
        except KeyError:
            return None

    @staticmethod
    def get_widget_value(widget_name, widget_category, arg="value"):
        """
        By default, this method returns the value belonging to key arg = "value" Essentially, the value that the
        streamlit session state normally assigns to the widget key. However, optional arg can be used to return any value
        desired.
        """
        try:
            return st.session_state["config"][widget_category][widget_name][arg]
        except KeyError:
            return None

    @staticmethod
    def set_widget_value(widget_name: str, widget_category: str, updated_arg_value, arg: str= "value") -> bool:
        """
        Update arguments to existing widget configs.
        """
        try:
            widget_config = st.session_state["config"][widget_category][widget_name]
            current = widget_config[arg]
        except KeyError as e:
            raise KeyError(
                f"Missing path while updating: {widget_category!r}/{widget_name!r}/{arg!r}"
            ) from e

        if arg == "extra_callback" and updated_arg_value is not None and not callable(updated_arg_value):
                raise TypeError(f"extra_callback must be a callable, got {type(updated_arg_value).__name__} instead.")

        if updated_arg_value != widget_config[arg]:
            widget_config[arg] = updated_arg_value
            #print(f"Updated {widget_category}|{widget_name}:"
                  #f" set {arg} to: {updated_arg_value}")
            return True
        return False


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