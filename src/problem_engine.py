import random
from abc import ABC
from fractions import Fraction
from dataclasses import dataclass
from typing import Union, Callable, Any
operator = {
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
    def __init__(self, range_ = None, data_type_ = None):
        self.range = range_
        self.data_type = data_type_

    def generate(self):
        if self.data_type == "ints":
            return [random.randint(lower, upper) for lower, upper in self.range]
        else:
            return [Fraction(random.randint(lower * d, upper * d), d)
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
    positive_answers_only: bool = False
    answer: Any = None
    operator: Any = None

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
        self.operator = operator[self.type]
        self.modify_problem()
        return self.answer

    def modify_problem(self):
        if self.type == "add":
            self.operator = operator["add"]
            self.answer = self.left + self.right
            return

        if self.positive_answers_only:
            self.left, self.right = max(self.left, self.right), min(self.left, self.right)

        self.answer = self.left - self.right

@register("mult")
@register("div")
@dataclass
class MultProblem(Problem):
    def operate(self):
        self.operator = operator[self.type]
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

def make_problem(type_, left_, right_, positive_answers_only_=False):
    return PROBLEM_DISPATCH[type_](left=left_, right=right_, type=type_, positive_answers_only=positive_answers_only_)

class CoreProblem:
    def __init__(self, range_ = None, problem_type_ = None, dtype_ = None, positive_answers_only_ = False):
        self.range = range_
        self.problem_type = problem_type_
        self.data_type = dtype_
        self.generator = Generator(range_=self.range, data_type_=self.data_type)
        self.answer = None
        self.Problem = None
        self.positive_answers_only = positive_answers_only_

    def calc(self):
        """Generate a problem instance and compute its answer."""

        left, right = self.generator.generate()
        self.Problem = make_problem(self.problem_type, left, right, self.positive_answers_only)
        self.answer = self.Problem.operate()

    def info(self):
        return to_dict(self)

    @staticmethod
    def calc_theoretical_range(type_, ranges_, positive_answers_only: Union[bool, Callable[[], bool]]=False):

        # example:
        # (l1 -> r1) + (l2 ->  r2) = (min_ ->  max_)
        pos = positive_answers_only() if callable(positive_answers_only) else positive_answers_only
        print(f"we entered, pos is {pos}")
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

# Example
if __name__ == "__main__":
    ranges = [[1,99], [1,99]]
    myProblem = CoreProblem(range_=ranges, problem_type_="mult", dtype_="ints")
    myProblem.calc()
    print(myProblem.info())














