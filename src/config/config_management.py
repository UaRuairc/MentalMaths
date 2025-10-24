import streamlit as st
import inspect
from src.ui.widgets import custom_input_box

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
            raise RuntimeError(f"The session state is not currently configured.")

        if ConfigManager.is_registered(widget_name, widget_category):
            print(f"widget {widget_name} of category {widget_category} is already registered.")
            return False

        config = ConfigManager.new_config(widget_name, widget_category, **overrides)

        name = config["name"]
        category = config["widget_category"]

        config.pop("name")
        st.session_state["config"][category][name] = config

        if not st.session_state["suppress"]:
            print("\n Added config to session state: {}\n".format(st.session_state["config"][category][name] ))

        return True

    @staticmethod
    def remove_widget(widget_name: str, widget_category: str):
        """
        For a given widget of category widget_category, removes the widget's config from the streamlit session state.
        """

        if ConfigManager.is_registered(widget_name, widget_category):
            st.session_state["config"][widget_category].pop(widget_name)

    @staticmethod
    def new_config(widget_name: str, widget_category: str, **overrides):
        """
        Generate a widget config in dictionary format.

        First, for a given UI framework, this method generates the baseline config via introspection of the widget callable's
        signature and sets defaults. Afterwards, we extend the config beyond baseline. Any overrides are applied at the very end.

        Args:
            widget_name: The natural name, or label, for the widget. The widget key is constructed from the widget name.
            widget_category: The category of the widget. This must be an existing widget from a given library.
            **overrides: Additional overrides to overwrite any defaults.

        Returns:
            dict[str, Any]: The finished config dictionary
        """
        framework = "streamlit"
        base_config = ConfigManager.base_config(widget_category=widget_category, framework=framework)

        base_config_defaults = {
            "label": f"{widget_name}",
            "key": f"{widget_name}_{widget_category}",
        }

        base_config.update(base_config_defaults)

        additional_config = {
            "widget_category": widget_category,
            "name": widget_name,
            "on_change": None,
            "extra_callback": None
        }

        config = {}
        config.update(base_config)
        config.update(additional_config)

        # some streamlit widgets do not have a `value` parameter
        #
        # MakeWidget generically uses the value param to store info on how to rebuild the widget, whether the widget has
        # a `value` parameter or not. MakeWidget then updates the config so "value" is renamed to whatever key that widget uses
        if "value" not in config:
            config["value"] = None
        if widget_category == "number_input_box":
            config["value"] = 0
        # Apply overrides

        config.update(overrides)
        return config


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
    def base_config(widget_category: str, framework: str= "streamlit"):
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

        base_config = {}
        for param_name, param in sig.parameters.items():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            if param.default is not inspect.Parameter.empty:
                base_config[param_name] = param.default
                continue

            # doesn't have a default, needs to be set, assume user provides overrides.
            base_config[param_name] = None

        return base_config

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
