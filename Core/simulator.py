import numbers
import random
from abc import ABC, abstractmethod
from typing import Tuple, Any
from fractions import Fraction

operator = {
    "add_ints": "+",
    "add_floats": "+",
    "sub_ints": "-",
    "sub_floats": "-",
    "mult_ints": chr(215),
    "div_ints": chr(247),
    "mult_floats": chr(215),
    None: None
}

def to_dict(obj):
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, '__dict__'):
        return {k: to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [to_dict(v) for v in obj]
    else:
        return obj
class Generator:

    # r is a list of lists. Each list represents a range.
    # for example:
    # r = [[2,6], [4,10]]
    # Generator two numbers a and b such that
    # 2 <= a <= 6 and 4 <= b <= 10

    def __init__(self, r_integers = None, r_floats = None, r_fractions = None):
        self.r_integers = r_integers
        self.r_floats = r_floats
        self.r_fractions = r_fractions
        # self.integers = []
        # self.floats = []
        # self.fractions = []

    def generate_ints(self) -> list:

        # random.seed()

        # for lower, upper in self.r_integers:
            # self.integers.append(random.randint(lower, upper))

        return [random.randint(lower, upper) for lower, upper in self.r_integers]



    def generate_floats(self) -> list:

        #random.seed()

        # for lower, upper in self.r_floats:
            # self.floats.append(random.uniform(lower, upper))
        return [random.uniform(lower, upper) for lower, upper in self.r_floats]




    def generate_fractions(self) -> list:

        #random.seed()

        ### temporary implementation of fractions.. ###

        return [Fraction(random.randint(lower * d, upper * d), d)
                for lower, upper in self.r_fractions
                for d in [random.randint(1, 9)]
                ]



class Problem(ABC):

    def __init__(self, numbers = None):
        self.numbers = numbers
        self.type = None
        self.left = None
        self.right = None
        self.operator = None


    @abstractmethod
    def operate(self) -> Any:
        pass

class AddIntsProblem(Problem):
    def __init__(self, numbers):
        super().__init__(numbers)
        self.type = "add_ints"
        self.operator = operator["add_ints"]
        if len(numbers) == 2:
            self.left = numbers[0]
            self.right = numbers[1]

    def operate(self):

        return sum(self.numbers)

class AddFracsProblem(Problem):
    def __init__(self, numbers):
        super().__init__(numbers)
        self.type = "add_fracs"
        if len(numbers) == 2:
            self.left = numbers[0]
            self.right = numbers[1]

    def operate(self):

        return sum(self.numbers)

class MultInts(Problem):
    def __init__(self, numbers):
        super().__init__(numbers)
        self.type = "mult_ints"
        if len(numbers) == 2:
            self.left = numbers[0]
            self.right = numbers[1]

    def operate(self):

        return self.left * self.right




class CoreProblem:

    def __init__(self, r_integers = None, r_floats = None, r_fractions = None, type = None):
        self.r_integers = r_integers
        self.r_floats = r_floats
        self.r_fractions = r_fractions
        self.type = type
        self.generator = Generator(r_integers= r_integers, r_floats = r_floats, r_fractions = r_fractions)
        self.answer = None
        self.Problem = None


    def calc(self):

        if self.type == "add_ints" or "add_fracs":

            assert self.r_integers is not None or self.r_fractions is not None, "addition requires integers or fractions"

            if self.type == "add_ints":
                # print(self.r_integers)
                self.Problem = AddIntsProblem(self.generator.generate_ints())
            else:
                self.Problem = AddFracsProblem(self.generator.generate_fractions())

        if self.type == "mult_ints":

            assert self.r_integers is not None, "multiplication requires integers"

            self.Problem = MultInts(self.generator.generate_ints())


        self.answer = self.Problem.operate()

    # def result(self):
        # print(f"{self.Problem.left} + {self.Problem.right}")

    def info(self):
        return to_dict(self)


ranges = [[1,7], [2,7]]
myProblem = CoreProblem(r_integers = ranges, r_floats = None, r_fractions = ranges, type = "mult_ints")
myProblem.calc()
# myProblem.result()













