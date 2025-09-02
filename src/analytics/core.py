import pandas as pd
from src.database.queries import Queries

def last_session_problem_data(session_id: str=None):
    q = Queries()
    if session_id is None:
        response = q.fetch_session()
        session_data = response.data
        session_id = session_data[0]["session_id"]

    response = q.fetch_problems(session_id=session_id)
    problem_data = response.data
    problem_data = pd.DataFrame(problem_data)

    return problem_data