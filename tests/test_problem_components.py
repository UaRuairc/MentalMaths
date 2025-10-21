# tests/test_problem_engine.py
import pytest
from game.content.problem_engine import Question
from tests.utils import static_seeds, static_ranges, EXPECTED_OPERANDS, ops

SEEDS = static_seeds()
RANGES = static_ranges()
TEST_CASES = [(op, seed, ranges, i%8) for op in ops for i, (seed,ranges) in enumerate(zip(SEEDS[op], RANGES[op]))]


@pytest.mark.parametrize("op, seed, ranges, i", TEST_CASES)
def test_problem_components(op, seed, ranges, i):

    l1, r1 = ranges
    l2, r2 = l1 + 1000, r1 + 1000

    q = Question(range_=((l1, r1), (l2, r2)), op_=op, seed=seed, dtype_="ints")
    q.prepare(problem_id=i)
    q.Problem.solve()
    q.answer = q.Problem.eff_answer

    components = q.Problem._eff_components
    assert (components.left, components.right) == EXPECTED_OPERANDS[op][i]
