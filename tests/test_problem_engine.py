# tests/test_problem_engine.py
import pytest
from src.problem_management.problem_engine import Question

#leftrights = [[2, 1004], [6, 1003], [4, 1008], [9, 1007], [103, 1126], [177, 1146], [193, 1164], [135, 1183], [4, 1005], [3, 1004], [6, 1008], [4, 1009], [131, 1173], [138, 1127], [198, 1179], [134, 1127], [5, 1002], [2, 1003], [7, 1004], [4, 1006], [136, 1171], [133, 1130], [176, 1110], [109, 1183], [5, 1004], [4, 1004], [6, 1004], [7, 1006], [162, 1167], [187, 1149], [176, 1157], [113, 1127]]
#answers = [2008, 6018, 4032, 9063, 115978, 202842, 224652, 159705, 4020, 3012, 6048, 4036, 153663, 155526, 233442, 151018, 5010, 2006, 7028, 4024, 159256, 150290, 195360, 128947, 5020, 4016, 6024, 7042, 189054, 214863, 203632, 127351]
modifiers = {
            "pos_answers_only": False,
            "fade_problem": False,
    }
ops = [
        "add",
        "sub",
        "mult",
        "div"
    ]

EXPECTED_DETAILS = {
    "add": [(2, 1004, 1006), (6, 1003, 1009), (4, 1008, 1012), (9, 1007, 1016), (103, 1126, 1229), (177, 1146, 1323), (193, 1164, 1357), (135, 1183, 1318)],
    "sub": [(4, 1005, -1001), (3, 1004, -1001), (6, 1008, -1002), (4, 1009, -1005), (131, 1173, -1042), (138, 1127, -989), (198, 1179, -981), (134, 1127, -993)],
    "mult": [(5, 1002, 5010), (2, 1003, 2006), (7, 1004, 7028), (4, 1006, 4024), (136, 1171, 159256), (133, 1130, 150290), (176, 1110, 195360), (109, 1183, 128947)],
    "div": [(5020, 5, 1004), (4016, 4, 1004), (6024, 6, 1004), (7042, 7, 1006), (189054, 162, 1167), (214863, 187, 1149), (203632, 176, 1157), (127351, 113, 1127)]
}

EXPECTED_OPERANDS = {
    "add": [(details[0], details[1]) for details in EXPECTED_DETAILS["add"]],
    "sub": [(details[0], details[1]) for details in EXPECTED_DETAILS["sub"]],
    "mult": [(details[0], details[1]) for details in EXPECTED_DETAILS["mult"]],
    "div": [(details[0], details[1]) for details in EXPECTED_DETAILS["div"]]
}

EXPECTED_ANSWERS = {
    "add": [details[2] for details in EXPECTED_DETAILS["add"]],
    "sub": [details[2] for details in EXPECTED_DETAILS["sub"]],
    "mult": [details[2] for details in EXPECTED_DETAILS["mult"]],
    "div": [details[2] for details in EXPECTED_DETAILS["div"]]
}

def static_seeds():
    """Initialise the seeds for each operation.

    DO NOT CHANGE THIS FUNCTION.
    It is used to generate the expected results for the tests.
    """
    SEEDS = {
        "add": [],
        "sub": [],
        "mult": [],
        "div": []
    }

    for i in range(100, 108):
        SEEDS["add"].append(i)
        SEEDS["sub"].append(i + 10)
        SEEDS["mult"].append(i + 20)
        SEEDS["div"].append(i + 30)

    return SEEDS

def static_ranges():
    """Initialise the seeds for each operation.

        DO NOT CHANGE THIS FUNCTION.
        It is used to generate the expected results for the tests.
        """

    RANGES = {
        "add": [],
        "sub": [],
        "mult": [],
        "div": []
    }

    for i in range(1, 5):
        RANGES["add"].append((i, i + 5))
        RANGES["sub"].append((i, i + 5))
        RANGES["mult"].append((i, i + 5))
        RANGES["div"].append((i, i + 5))
    for i in range(101, 105):
        RANGES["add"].append((i, 2 * i))
        RANGES["sub"].append((i, 2 * i))
        RANGES["mult"].append((i, 2 * i))
        RANGES["div"].append((i, 2 * i))
    return RANGES

SEEDS = static_seeds()
RANGES = static_ranges()

@pytest.mark.parametrize("op, seed, ranges, i", [(op, seed, ranges, i%8) for op in ops for i, (seed,ranges) in enumerate(zip(SEEDS[op], RANGES[op])) ])
def test_problem_generation(op, seed, ranges, i):

    modifiers["pos_answers_only"] = False

    l1, r1 = ranges
    l2, r2 = l1 + 1000, r1 + 1000

    q = Question(range_ = ((l1, r1), (l2, r2)), op_=op, seed=seed, dtype_ = "ints", modifiers=modifiers)
    q.calc()

    assert q.answer == EXPECTED_ANSWERS[op][i]

@pytest.mark.parametrize("op, seed, ranges, i", [(op, seed, ranges, i%8) for op in ops for i, (seed,ranges) in enumerate(zip(SEEDS[op], RANGES[op])) ])
def test_left_right_operands(op, seed, ranges, i):

    modifiers["pos_answers_only"] = False

    l1, r1 = ranges
    l2, r2 = l1 + 1000, r1 + 1000

    q = Question(range_=((l1, r1), (l2, r2)), op_=op, seed=seed, dtype_="ints", modifiers=modifiers)
    q.calc()

    assert (q.Problem.left, q.Problem.right) == EXPECTED_OPERANDS[op][i]

@pytest.mark.parametrize("op, seed, ranges, i", [(op, seed, ranges, i%8) for op in ops for i, (seed,ranges) in enumerate(zip(SEEDS[op], RANGES[op])) ])
def test_modifier_pos_answers_only(op, seed, ranges, i):

    l1, r1 = ranges
    l2, r2 = l1 + 1000, r1 + 1000

    modifiers["pos_answers_only"] = True

    q = Question(range_ = ((l1, r1), (l2, r2)), op_=op, seed=seed, dtype_ = "ints", modifiers=modifiers)
    q.calc()


    assert q.answer == abs(EXPECTED_ANSWERS[op][i])


