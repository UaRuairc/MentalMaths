import random
from abc import ABC, abstractmethod
from fractions import Fraction
from dataclasses import dataclass
from typing import Any
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
    left: Any
    right: Any
    operator: str
    def operate(self) -> Any:
        pass

def register(type_):
    """Decorator: remember <class> under the string <kind>."""
    def _wrap(cls):
        PROBLEM_DISPATCH[type_] = cls
        return cls
    return _wrap

@register("add")
@dataclass
class AddProblem(Problem):
    def operate(self):
        return self.left + self.right

@register("sub")
@dataclass
class SubProblem(Problem):
    type = "sub"
    def operate(self):
        return self.left - self.right

@register("mult")
@dataclass
class MultProblem(Problem):
    type = "mult"
    def operate(self):
        return self.left * self.right

@register("div")
@dataclass
class DivProblem(Problem):
    type = "div"

    def operate(self):
        # multiplication but backwards.
        mult_answer = self.left * self.right

        # choose the divisor randomly
        divisor_and_answer = [self.left, self.right]
        random.shuffle(divisor_and_answer)
        divisor, div_answer = divisor_and_answer

        # update
        self.left = mult_answer
        self.right = divisor
        return div_answer


def make_problem(type_, left_, right_, operator_):
    return PROBLEM_DISPATCH[type_](left_, right_, operator_)



class CoreProblem:
    def __init__(self, range_ = None, problem_type_ = None, dtype_ = None):
        self.range = range_
        self.problem_type = problem_type_
        self.data_type = dtype_
        self.generator = Generator(range_=self.range, data_type_=self.data_type)
        self.answer = None
        self.Problem = None


    def calc(self):
        """Generate a problem instance and compute its answer."""

        left, right = self.generator.generate()
        self.Problem = make_problem(self.problem_type, left, right, operator[self.problem_type])
        self.answer = self.Problem.operate()

    def info(self):
        return to_dict(self)

# Example
if __name__ == "__main__":
    ranges = [[1,99], [1,99]]
    myProblem = CoreProblem(range_=ranges, problem_type_="mult", dtype_="ints")
    myProblem.calc()
    print(myProblem.info())














