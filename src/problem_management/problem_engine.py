import random
from abc import ABC
from fractions import Fraction
from dataclasses import dataclass
from typing import Union, Callable, Any
from datetime import datetime, timezone
import time
op_string = {
    "add": "+",
    "sub": "-",
    "mult": chr(215),
    "div": chr(247),
}

def to_dict(obj):
    """Recursively convert objects to dictionaries or lists."""
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, '__dict__'):
        return {k: to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [to_dict(v) for v in obj]
    else:
        return obj

class Generator:
    """ generate random numbers based on the range of values the user chooses
        ** removed generation of non-integers for now, may add back later
    """
    def __init__(self, range_ = None, dtype_ = None, seed = None):
        self.range = range_
        self.dtype = dtype_
        self.rng = random.Random(seed) if seed is not None else random.Random()

    def generate(self):
        if self.dtype == "ints":
            return [self.rng.randint(lower, upper) for lower, upper in self.range]
        else:
            return [Fraction(self.rng.randint(lower * d, upper * d), d)
                for lower, upper in self.range
                for d in [random.randint(1, 9)]
                ]

PROBLEM_DISPATCH = {}

@dataclass
class Problem(ABC):
    """create a base class (and registry below) """
    left: Any
    right: Any
    type: Any
    invert_operation: bool = False
    modifiers: dict = None
    answer: Any = None
    op: Any = None

    def operate(self) -> Any:
        pass
    def modify_problem(self) -> Any:
        pass

def register(type_):
    """Return a class decorator that registers the decorated class

        """
    def _wrap(cls):
        PROBLEM_DISPATCH[type_] = cls
        return cls
    return _wrap

@register("add")
@register("sub")
@dataclass
class AddProblem(Problem):
    """
         This is baseline addition.
         
         We can convert it to a subtraction problem
         if we convert it to a subtraction problem, let the user decide:
         "do I want to deal with negative results?"

         eg if 
         self.left = 20
         self.right = 50
         then 20-50 = -30

         alternatively, if the user prefers, we always give them:
         50-20 = 30
    """

    def operate(self):
        self.op = op_string[self.type]
        self.modify_problem()
        return self.answer

    def modify_problem(self):
        if self.type == "add":
            self.answer = self.left + self.right
            return

        if self.modifiers["pos_answers_only"]:
            self.left, self.right = max(self.left, self.right), min(self.left, self.right)

        self.answer = self.left - self.right

@register("mult")
@register("div")
@dataclass
class MultProblem(Problem):
    def operate(self):
        self.op = op_string[self.type]
        self.modify_problem()
        return self.answer

    def modify_problem(self):
        if self.type == "mult":
            self.answer = self.left * self.right
            return

        """ for a division problem that results in integers we need to essentially reverse a multiplication problem """
        # self.right is the quotient
        # self.left is the divisor
        # dividend / divisor = quotient
        dividend = self.left * self.right
        divisor = self.left
        quotient = self.right
        # for display update left / right values
        self.left = dividend
        self.right = divisor
        self.answer = quotient

def make_problem(type_, left_, right_, modifiers_=False):
    return PROBLEM_DISPATCH[type_](left=left_, right=right_, type=type_, modifiers=modifiers_)

class Question:

    """
    In the future we may have different game modes, e.g., multiple choice

                    5 + 5 = ?

    [ans1]      [ans2]      [ans3]      [ans3]

    In which case we may need to make multiple problem objects of different problem types, and this class wraps them all
    """
    def __init__(self, range_ = None, op_ = None, dtype_ = None, modifiers = None, seed = None):
        self.range = range_
        self.op = op_
        self.dtype = dtype_
        self.modifiers = modifiers
        self.generator = Generator(range_=self.range, dtype_=self.dtype, seed=seed)
        self.answer = None
        self.Problem = None

        self.problem_start_time = datetime.now(timezone.utc)
        self.problem_start_perf_counter = time.perf_counter()

    def calc(self):
        """Generate a problem instance and compute its answer."""

        left, right = self.generator.generate()
        self.Problem = make_problem(self.op, left, right, self.modifiers)
        self.answer = self.Problem.operate()

    def info(self):
        return to_dict(self)

    def snapshot(self, last_event):
        """
        Create a snapshot of this Question instance.
        """

        data = {
            "problem_type": f"{self.op}_{self.dtype}",
            "created_at": str(self.problem_start_time),
            "left_operand": self.Problem.left,
            "right_operand": self.Problem.right,
            "answer": self.answer,
            "status": "unanswered",
            "modifiers": self.modifiers,
            "is_correct": None,
            "event": last_event
        }
        if last_event == "user_answer_validated":
            data["answer_ms"] = self.time_elapsed_ms()
            data["is_correct"] = True

        return data

    @staticmethod
    def calc_theoretical_range(type_, ranges_: Union[tuple, Callable[[], tuple]], pos_answers_only: Union[bool, Callable[[], bool]]=False):

        # example:
        # (l1 -> r1) + (l2 ->  r2) = (min_ ->  max_)
        pos = pos_answers_only() if callable(pos_answers_only) else pos_answers_only
        ranges_ = ranges_() if callable(ranges_) else ranges_

        l1, r1 = ranges_[0]
        l2, r2 = ranges_[1]
        if type_ == "add":

            min_ = l1 + l2
            max_ = r1 + r2

        elif type_ == "subtract":
            min_ = l1 - r2
            max_ = r1 - l2

            if pos:

                if min_ <= 0 and max_ <= 0:
                    print("cannot be positive!!")
                    min_, max_ = 0, 0

                elif min_<=0 and max_>0:
                    min_ = 0

                else:
                    pass
        else:
            min_ = l1 * l2
            max_ = r1 * r2

        return min_, max_

    def time_elapsed_ms(self):
        elapsed = time.perf_counter() - self.problem_start_perf_counter
        elapsed_ms = elapsed * 1000
        return int(round(elapsed_ms))

# Example
if __name__ == "__main__":
    ranges = [[1,99], [1,99]]
    myProblem = Question(range_=ranges, op_="mult", dtype_="ints", modifiers=None)
    myProblem.calc()
    print(myProblem.info())














