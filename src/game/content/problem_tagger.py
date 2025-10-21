import math
from typing import Callable, TypedDict, TYPE_CHECKING
from dataclasses import replace

if TYPE_CHECKING:
    from src.game.content.problem_engine import Problem


def count_number_of_carries(left, right):
    """
    Calculates and returns the number of carry operations required when adding two integers digit by digit.
    """
    carry_count = 0
    current_carry = 0
    while left or right:
        left, left_remainder = divmod(left, 10)
        right, right_remainder = divmod(right, 10)
        if left_remainder + right_remainder + current_carry >= 10:
            carry_count += 1
            current_carry = 1
        else:
            current_carry = 0
    return carry_count

def count_number_of_borrows(left, right):
    """
    Counts and returns the number of borrows that occur during digit-wise subtraction of two numbers.
    """
    borrow_count = 0
    current_borrow = 0

    while left or right:
        left, left_remainder = divmod(left, 10)
        right, right_remainder = divmod(right, 10)

        left_remainder -= current_borrow
        if left_remainder < right_remainder:
            borrow_count += 1
            current_borrow = 1
        else:
            current_borrow = 0

    return borrow_count

def is_power_of_2(n):
    """
    Determines if a given integer is a power of 2 using a bitwise trick.
    Returns a tuple:
        - A boolean indicating whether the number is a power of 2 (True or False).
        - The base (None if not a power of 2)
        - The exponent (None if not a power of 2)

        The reason for this is, in the future we may need prime factor info, thus this future proofs the code
    """

    x = abs(n)  # just want to check if someone can use power for 2 tricks, sign doesnt matter
    if x == 0:
        return False, None, None

    if (x & (x - 1)) == 0:
        exponent = x.bit_length() - 1
        return True, 2, exponent

    return False, None, None

def digit_count(n: int):
    n = abs(int(n))
    if n == 0:
        return "SINGLE_DIGIT"

    count = int(math.log10(n)) + 1

    return count

def digit_tag(count: int):
    if count == 1:
        tag = "SINGLE_DIGIT"
    elif count == 2:
        tag = "DOUBLE_DIGIT"
    elif count == 3:
        tag = "TRIPLE_DIGIT"
    else:
        tag = "HIGH_DIGIT"

    return tag

def last_n_digits(x, n):
    """
    Calculates the last n digits of a given integer x.
    """
    return abs(x) % 10 ** n

def digit_sum(n):
    return sum(int(d) for d in str(abs(int(n))))

def trick_check_complement_10_pairs(low, high):
    if not (low >= 10 and high <= 100):
        return False

    last_digits_sum_to_zero = ((low % 10) + (high % 10) == 10)
    same_first_digit = (low // 10 == high // 10)

    if same_first_digit and last_digits_sum_to_zero:
        return True

    return False

def get_core_addition_tags(left, right, ans, low, high, equal_operands):
    tags = set()
    features = {}

    carry_count = count_number_of_carries(left, right)
    if carry_count > 0:
        tags.add(f"CARRY_REQUIRED")
        features["carry_count"] = carry_count

    return tags, features

def get_core_subtraction_tags(left, right, ans, low, high, equal_operands):
    tags = set()
    features = {}

    borrow_count = count_number_of_borrows(left, right)
    if borrow_count > 0:
        tags.add(f"BORROW_REQUIRED")
        features["borrow_count"] = borrow_count

    return tags, features

def get_core_multiplication_tags(left, right, ans, low, high, equal_operands):
    tags = set()
    features = {}

    SIMPLE_MULTIPLICANDS = {5, 9, 10, 11, 25, 50, 99, 101, 125}
    simple_multiplicands = []
    if left in SIMPLE_MULTIPLICANDS: simple_multiplicands.append(left)
    if right in SIMPLE_MULTIPLICANDS: simple_multiplicands.append(right)
    if simple_multiplicands:
        tags.add("SIMPLE_MULTIPLICAND")
        features["simple_multiplicands"] = simple_multiplicands

    if equal_operands:
        tags.add("PERFECT_SQUARE")

    # tags for standard classification
    if low <= 2:
        tags.add("TRIVIAL_TIMES_TABLES")
    elif high <= 9:
        tags.add("EASY_TIMES_TABLES")
    elif high <= 12:
        tags.add("MEDIUM_TIMES_TABLES")
    elif high <= 24:
        tags.add("HARD_TIMES_TABLES")
    else:
        tags.add("EXTENDED_TIMES_TABLES")

    if trick_check_complement_10_pairs(low, high):
        tags.add("COMPLEMENT_10_PAIRS")

    return tags, features

def get_core_division_tags(dividend, divisor, ans, low, high, equal_operands):
    tags = set()
    features = {}

    return tags, features

OP_TAGGERS: dict[str, Callable] = {
    "add": get_core_addition_tags,
    "sub": get_core_subtraction_tags,
    "mult": get_core_multiplication_tags,
    "div": get_core_division_tags,
}

class TagData(TypedDict):
    terms: dict
    operator: dict
    general: dict

def problem_tagger(p: "Problem", eff=True) -> TagData:
    """

    Generate tags for a problem

    """
    if eff:
        components = replace(p._eff_components)
    else:
        components = replace(p.components)

    left = components.left
    op = components.op
    right = components.right

    ans = p.eff_answer
    dtype = p.dtype

    enabled_modifiers = p.mod_log.get("stats", {}).keys()

    info = {
        "terms":{
            "left": {
                "val": left,
                "tags": set(),
                "features": {}
            },
            "right": {
                "val": right,
                "tags": set(),
                "features": {}
            },
            "ans": {
                "val": ans,
                "tags": set(),
                "features": {}
            },
        },
        "operator":{
            "tags": set(),
            "features": {}
        },
        "general":{
            "tags": set(),
            "features": {}
            }
    }

    low = min(abs(left), abs(right))
    high = max(abs(left), abs(right))

    equal_operands = (low == high)  # abs taken

    for term in info["terms"].values():

        val = term["val"]

        d = digit_count(val)
        term["tags"].add(digit_tag(d))
        term["features"]["digit_count"] = d

        parity = "EVEN" if val % 2 == 0 else "ODD"
        term["tags"].add(parity)

        check, _, _ = is_power_of_2(val)
        if check:
            term["tags"].add("POWER_OF_2")

    # operation specific
    tagger = OP_TAGGERS[op]
    if tagger:
        op_tags, op_features = tagger(left, right, ans, low, high, equal_operands)
        info["operator"]["tags"] |= op_tags
        info["operator"]["features"].update(op_features)

    if equal_operands:
        info["general"]["tags"].add("EQUAL_OPERANDS")

    for mod_id in enabled_modifiers:
        info["general"]["tags"].add(f"MOD_{mod_id.upper()}")

    info["general"]["tags"].add(dtype)

    tag_data = TagData(terms = info["terms"], operator = info["operator"], general = info["general"])

    return tag_data