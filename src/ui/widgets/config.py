import streamlit as st
import inspect
from dataclasses import dataclass, field, InitVar
from typing import Any, Optional, Dict
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
