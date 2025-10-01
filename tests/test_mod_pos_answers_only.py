# tests/test_problem_engine.py
import pytest
from game.content.problem_engine import Question
from game.content.modifiers import ModManager as mm
from tests.utils import static_seeds, static_ranges, ops, EXPECTED_ANSWERS

SEEDS = static_seeds()
RANGES = static_ranges()
TEST_CASES = [(op, seed, ranges, i%8) for op in ops for i, (seed,ranges) in enumerate(zip(SEEDS[op], RANGES[op]))]

@pytest.mark.parametrize("op, seed, ranges, i", TEST_CASES)
def test_modifier_pos_answers_only(op, seed, ranges, i):

    l1, r1 = ranges
    l2, r2 = l1 + 1000, r1 + 1000


    q = Question(range_ = ((l1, r1), (l2, r2)), op_=op, seed=seed, dtype_ = "ints")
    q.prepare()
    mm.mod("new_problem_created", q.Problem, ["pos_answers_only"])
    q.Problem.solve()
    q.answer = q.Problem.eff_answer


    assert q.answer == abs(EXPECTED_ANSWERS[op][i])


