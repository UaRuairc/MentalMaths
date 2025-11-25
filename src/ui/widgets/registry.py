import streamlit as st
from src.ui.widgets.config import WidgetConfig

class WidgetRegistry:
    """
    Handles widget config generation and mutation.
    """

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
