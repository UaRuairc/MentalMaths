import streamlit as st
import inspect
from dataclasses import dataclass, field, InitVar
from typing import Any, Optional, Dict, Callable
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

@dataclass(frozen=True)
class WidgetSpec:
    settable: bool
    value_param: str
    transform: Optional[Callable[[Any, dict], Any]] =  lambda val, params: val



WIDGET_SPECS = {
    "streamlit": {
        "checkbox": WidgetSpec(True, "value"),
        "slider": WidgetSpec(True, "value"),
        "number_input_box": WidgetSpec(True, "value"),
        "segmented_control": WidgetSpec(True, "default", lambda default, params: params["options"][default]),
        "text_input_boxes": WidgetSpec(True, "value"),
        "buttons": WidgetSpec(False, "value"),
        "select_box": WidgetSpec(True, "index", lambda index, params: params["options"][index]),
        "title_box": WidgetSpec(True, "body"),
    },
    "custom": {
        "number_input_box": WidgetSpec(False, "user_response"),
    }
}


@dataclass
class WidgetConfig:
    name: str
    category: str
    framework: str = "streamlit"
    init_config: InitVar[Optional[Dict[str, Any]]] = None

    _params: dict = field(default_factory=dict)
    _framework_keys: set = field(default_factory=set)

    def __post_init__(self, init_config = None):

        init_config = (init_config or {}).copy()

        if "framework" in init_config:
            self.framework = init_config["framework"]
            init_config.pop("framework")

        if ("value" != self.spec.value_param) and ("value" in init_config and self.spec.value_param in init_config):
            raise ValueError(f"Cannot set both 'value' and '{self.spec.value_param}' in initial config.")

        if "value" in init_config:
            init_config[self.spec.value_param] = init_config.pop("value")

        base_framework_config = build_framework_config(widget_category=self.category, framework=self.framework)
        base_extended_config = build_extended_config(name=self.name, category=self.category)
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
        params = params.copy()
        if ("value" != self.spec.value_param) and ("value" in params and self.spec.value_param in params):
            raise ValueError(f"Cannot set both 'value' and '{self.spec.value_param}' params.")

        if self.spec.value_param in params:
            self.set(params.pop(self.spec.value_param))
        elif "value" in params:
            self.set(params.pop("value"))


        self._params.update(params)

        return True

    def set(self, val):
        if self.spec.settable: self._params[self.spec.value_param] = val

    def _sync(self, value):
        self._params[self.spec.value_param] = value
        return True

    @property
    def value_param(self): return self.spec.value_param

    @property
    def value(self): return self._params.get(self.spec.value_param)

    def get(self, key, default=None): return self._params.get(key, default)

    @property
    def spec(self):
        return WIDGET_SPECS.get(self.framework, {}).get(self.category)

    @property
    def framework_params(self):
        return {key: self._params[key] for key in self._framework_keys}

    def __getitem__(self, key, default=None):
        if key == "value": key = self.spec.value_param
        return self._params.get(key, default)
    def __contains__(self, key):
        if key == "value": key = self.spec.value_param
        return key in self._params
    def __setitem__(self, key, value):
        if key == self.value_param or key == "value":
            self.set(value)
        else:
            self._params[key] = value
