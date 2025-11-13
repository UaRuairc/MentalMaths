import streamlit.components.v1 as components
import os
from src.ui.widgets.adapters import WIDGET_ADAPTERS
from src.ui.widgets.registry import WidgetRegistry

custom_input = components.declare_component(
    "custom_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)

def widget(name, category, **kwargs):
    adapter = WIDGET_ADAPTERS[WidgetRegistry.get_widget_config(name, category).framework]
    adapter.initialise(name, category)
    value = adapter.render(name, category, **kwargs)
    return value

def custom_input_box(problem_id_, correct_answer, key_, alignment_="center"):
    result = custom_input(
        key=key_,
        correctAnswer=str(correct_answer),
        alignment=alignment_,
        problemId=problem_id_,
    )
    if result is None:
        return ""
    return result
