import streamlit.components.v1 as components
import os
from src.config.config_management import StreamlitWidgetAdapter

custom_input = components.declare_component(
    "custom_input",
    path=os.path.join(os.getcwd(), "frontend", "build"),
)

def widget(name, category, **kwargs):
    StreamlitWidgetAdapter.initialise(name, category)
    StreamlitWidgetAdapter.render(name, category, **kwargs)

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
