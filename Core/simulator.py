import numbers
import random
from abc import ABC, abstractmethod
from typing import Tuple, Any
from fractions import Fraction


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

    def generate_ints(self):

        #random.seed()

        # for lower, upper in self.r_integers:
            # self.integers.append(random.randint(lower, upper))

        return [random.randint(lower, upper) for lower, upper in self.r_integers]

    def generate_floats(self):

        #random.seed()

        # for lower, upper in self.r_floats:
            # self.floats.append(random.uniform(lower, upper))
        return [random.uniform(lower, upper) for lower, upper in self.r_floats]




    def generate_fractions(self):

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

    @abstractmethod
    def operation(self) -> Any:
        pass

class AddIntsProblem(Problem):
    def __init__(self, numbers):
        super().__init__(numbers)
        self.type = "add_ints"
        if len(numbers) == 2:
            self.left = numbers[0]
            self.right = numbers[1]

    def operation(self):

        return sum(self.numbers)

class AddFracsProblem(Problem):
    def __init__(self, numbers):
        super().__init__(numbers)
        self.type = "add_fracs"
        if len(numbers) == 2:
            self.left = numbers[0]
            self.right = numbers[1]

    def operation(self):

        return sum(self.numbers)

class MultInts(Problem):
    def __init__(self, numbers):
        super().__init__(numbers)
        self.type = "mult_ints"
        if len(numbers) == 2:
            self.left = numbers[0]
            self.right = numbers[1]

    def operation(self):

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
                print(self.r_integers)
                self.Problem = AddIntsProblem(self.generator.generate_ints())
            else:
                self.Problem = AddFracsProblem(self.generator.generate_fractions())

        if self.type == "mult_ints":

            assert self.r_integers is not None, "multiplication requires integers"

            self.Problem = MultInts(self.generator.generate_ints())


        self.answer = self.Problem.operation()

    def result(self):
        print("results: ")
        print(self.answer)
        print(f"{self.Problem.left} * {self.Problem.right}")


ranges = [[1,7], [2,7]]
myProblem = CoreProblem(r_integers = ranges, r_floats = None, r_fractions = ranges, type = "mult_ints")
myProblem.calc()
myProblem.result()













