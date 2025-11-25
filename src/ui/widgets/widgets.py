import streamlit.components.v1 as components
import os
from src.ui.widgets.adapters import WIDGET_ADAPTERS
from src.ui.widgets.registry import WidgetRegistry

_custom_input = components.declare_component(
    "custom_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)

def custom_input(
        correct_answer,
        problem_id,
        key,
        on_change,
        alignment="center",
        user_response=None

    ):
    return _custom_input(correctAnswer = str(correct_answer), problemId=problem_id, alignment=alignment, key=key, on_change=on_change)

def widget(name, category, **kwargs):
    adapter = WIDGET_ADAPTERS[WidgetRegistry.get_widget_config(name, category).framework]
    adapter.initialise(name, category)
    value = adapter.render(name, category, **kwargs)
    return value

