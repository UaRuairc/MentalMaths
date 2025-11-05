import streamlit as st
import inspect
from src.ui.widgets import custom_input_box
from dataclasses import dataclass, field, InitVar
from typing import Any, Optional, Dict

CALLABLES = {
    "streamlit":{
        "checkbox": st.checkbox,
        "slider": st.slider,
        "number_input_box": st.number_input,
        "segmented_control": st.segmented_control,
        "text_input_boxes": st.text_input,
        "buttons": st.button,
        },
    "custom": {
        "custom_input_box": custom_input_box
    },
}

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

    if st.session_state["callables"].get(framework, None) is None:
        raise NotImplementedError(
            f"Framework {framework} is not supported. Currently, only streamlit is supported.")

    if st.session_state["callables"][framework].get(widget_category, None) is None:
        raise NotImplementedError(
            f"Widget category {widget_category} is not supported for framework {framework}.")

    widget_callable = CALLABLES[framework][widget_category]
    sig = inspect.signature(widget_callable)

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

def build_extended_config(name: str, category: str, framework: str = "streamlit"):
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
        base_framework_config = build_framework_config(widget_category=self.category, framework=self.framework)
        base_extended_config = build_extended_config(name=self.name, category=self.category, framework=self.framework)
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
            raise RuntimeError(f"The parameter linked to the framework's return value can only be modified via a widget action.")
        self._params.update(params)

    def set(self, value):
        if not self._framework_return_param:
            return

        self._params["value"] = value

    def get(self, key, default=None): return self._params.get(key, default)

    def __getitem__(self, key): return self._params[key]
    def __contains__(self, key): return key in self._params
    def __setitem__(self, key, value): self._params[key] = value



class ConfigManager:
    """
    Handles widget config generation and mutation.
    """

    @staticmethod
    def register(widget_name: str, widget_category: str, **overrides):
        """

        Create and register a widget config to the session state.
        Args:
            widget_name: The name you would like to give the widget. The widget's internal label will be set to this value. Additionally,
            the current convention is to name the widget's key in the dictionary as {widget_name}_{widget_category}.
            widget_category: The category of the widget you would like to create. This must be from an existing library.
            **overrides: Additional overrides to overwrite any defaults.
        Notes:
            This method will generate a config and then add it to the session state. See ConfigManager.generate_config()
            for further details.
        """

        if "config" not in st.session_state or not isinstance(st.session_state["config"], dict):
            raise RuntimeError(f"No config in session.")

        if ConfigManager.is_registered(widget_name, widget_category):
            print(f"widget {widget_name} of category {widget_category} is already registered.")
            return False

        # below is temporary until Widget() is refactored

        params = WidgetConfig(widget_name, widget_category, init_config=overrides)._params

        params.pop("name")

        st.session_state["config"][widget_category][widget_name] = params

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

        return widget_category in config and widget_name in config[widget_category]

    @staticmethod
    def get_config(widget_name, widget_category):
        """
        Return the config for a given widget.

        Args:
            widget_name: The name of the widget.
            widget_category: The category of the widget. This must be an existing widget from a given library.
        """
        if not ConfigManager.is_registered(widget_name, widget_category):
            raise KeyError(f"{widget_name} of category {widget_category } does not exist.")

        return st.session_state["config"][widget_category][widget_name]

    @staticmethod
    def get_value(widget_name, widget_category, arg="value"):
        """
        By default, this method returns the value belonging to key arg = "value" Essentially, the value that the
        streamlit session state normally assigns to the widget key. However, optional arg can be used to return any value
        desired.
        """
        return st.session_state["config"][widget_category][widget_name][arg]

    @staticmethod
    def set_value(widget_name: str, widget_category: str, updated_arg_value, arg: str= "value") -> bool:
        """
        Update arguments to existing widget configs.
        """
        if not ConfigManager.is_registered(widget_name, widget_category):
            raise KeyError(f"{widget_name} of category {widget_category} does not exist to update it")

        widget_config = st.session_state["config"][widget_category][widget_name]

        if arg not in widget_config:
            raise KeyError(f"arg {arg!r} is not in the {widget_name!r} config")

        if arg == "extra_callback" and updated_arg_value is not None and not callable(updated_arg_value):
                raise TypeError(f"extra_callback must be a callable, got {type(updated_arg_value).__name__} instead.")

        if updated_arg_value != widget_config[arg]:
            widget_config[arg] = updated_arg_value
            print(f"Updated {widget_category}|{widget_name}:"
                  f" set {arg} to: {updated_arg_value}")

        return True

    @staticmethod
    def remove_widget(widget_name: str, widget_category: str):
        """
        For a given widget of category widget_category, removes the widget's config from the streamlit session state.
        """

        if ConfigManager.is_registered(widget_name, widget_category):
            st.session_state["config"][widget_category].pop(widget_name)

    @staticmethod
    def add_param(widget_name, widget_category, new_arg, new_arg_value):
        """
        Add a new argument to the widget config in session state.
        This is used to add new arguments to existing widgets.
        """

        if not ConfigManager.is_registered(widget_name, widget_category):
            raise KeyError(f"{widget_name} of category {widget_category} does not exist to add a param to it.")

        widget_config = ConfigManager.get_config(widget_name, widget_category)

        if new_arg in widget_config:
            raise KeyError(f"{new_arg} already exists in {widget_category}. Use set_value to update it")

        widget_config[new_arg] = new_arg_value

        return