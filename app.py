import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import uuid
import sqlite3

# from Core import CoreProblem

def create_db():
    conn = sqlite3.connect("sessions.sqlite")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_data (
        session_id TEXT,
        session_state_data TEXT,
        PRIMARY KEY (session_id)
    )
    """)
    conn.commit()
    conn.close()

def load_from_database(session_id):
    conn = sqlite3.connect("sessions.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM session_data WHERE session_id = ?", (session_id,))
    data = cursor.fetchone()
    conn.close()

    return data

create_db()

query_params = st.query_params
session_id = query_params.get("session_id")

if not session_id:
    st.session_state["session_id"] = str(uuid.uuid4())
else:
    data = load_from_database(session_id)





st.title("Mental Maths Application")





st.markdown("Problem Types")
problem_type_settings = st.columns(3)
problem_range_settings = st.columns(3)




#for col in problem_type_settings:
    #addition = st.checkbox("Addition", value = True)

if "addition" not in st.session_state:
    with problem_type_settings[0]:
        addition = st.checkbox("Addition", key="add_ints", value=True)
        substraction = st.checkbox("Substraction", key="subtract_ints", value=True)
    with problem_type_settings[1]:
        multiplication = st.checkbox("Multiplication", key="mult_ints", value=True)
        division = st.checkbox("Division", key="div_ints", value=True)
    with problem_type_settings[2]:
        duration = st.number_input("Duration in seconds", key="duration_ints", value=120)



if addition:
    addition_range = st.slider("Range for addition problems", min_value=0, max_value=999, value=(1,99), step=1, key="add_ints_range")
if substraction:
    subtraction_range = st.slider("Range for subtraction problems", min_value=0, max_value=999, value=(1,99), step=1, key="sub_ints_range")
if multiplication:
    multiplication = st.slider("Range for multiplication problems", min_value=0, max_value=999, value=(1,99), step=1, key="mult_ints_range")
if division:
    division_range = st.slider("Range for division problems", min_value=0, max_value=999, value=(1,99), step=1, key="div_ints_range")









