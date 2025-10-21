import random
from abc import ABC
from fractions import Fraction
from dataclasses import dataclass, field, replace
from typing import Union, Callable, Any, TypedDict, Protocol
from datetime import datetime, timezone
import time
from src.game.content.problem_tagger import problem_tagger

op_symbols = {
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

PROBLEM_DISPATCH: dict[str, type["Problem"]] = {}

@dataclass(frozen=True)
class ProblemComponents:
    left: Any
    right: Any
    op: str

@dataclass
class Problem(ABC):
    """create a base class (and registry below) """
    dtype: str
    components: ProblemComponents
    id: int = None
    _eff_components: ProblemComponents = None
    base_answer: Any = None
    eff_answer: Any = None
    mod_log: dict = field(default_factory=dict)
    base_tags: Any = None
    eff_tags: Any = None

    _base_tagged: bool = field(default=False, init=False, repr=False)
    _eff_tagged: bool = field(default=False, init=False, repr=False)
    _solved: bool = field(default=False, init=False, repr=False)

    def __post_init__(self):
        self.solve_base()
        self._eff_components = replace(self.components)

    def solve_base(self):
        self.base_answer = self.operate(components=self.components)

    def solve(self):
        if self._solved:
            return
        self.eff_answer = self.operate(components = self._eff_components)
        self._solved = True
        return

    @property
    def base_tag_info(self):
        if not self._solved:
            raise ValueError("Problem must be solved before tagging.")

        if not self._base_tagged:
            self.base_tags = problem_tagger(self, eff=False)
            self._base_tagged = True

        return self.base_tags

    @property
    def eff_tag_info(self):
        if not self._solved:
            raise ValueError("Problem must be solved before tagging.")


        if not self._eff_tagged:
            self.eff_tags = problem_tagger(self, eff=True)
            self._eff_tagged = True

        return self.eff_tags



    def render_details(self, eff=True):
        symbol = self.op_symbol(self.components.op)
        if not eff:
            return self.components, symbol, self.base_answer, self.id

        self.solve()
        return self._eff_components, symbol, self.eff_answer, self.id

    def operate(self, components) -> Any:
        pass

    @staticmethod
    def op_symbol(op):
        return op_symbols[op]



def register(op):
    """
    Return a class decorator that registers the decorated class
    """
    def _wrap(cls):
        PROBLEM_DISPATCH[op] = cls
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

    def operate(self, components):
        if components.op == "add":
            return components.left + components.right
        else:
            return components.left - components.right

@register("mult")
@register("div")
@dataclass
class MultProblem(Problem):

    def __post_init__(self):
        """
        Division problems will always be generated via inverting a division problem.
        """
        if self.components.op == "div":
            dividend = self.components.left * self.components.right
            divisor = self.components.left
            self.components = replace(self.components, left = dividend, right = divisor)

        super().__post_init__()


    def operate(self, components):
        if components.op == "mult":
            return components.left * components.right
        else:
            return components.left / components.right

def make_problem(components, dtype_):
    return PROBLEM_DISPATCH[components.op](components=components, dtype=dtype_)

class Question:

    """
    In the future we may have different game modes, e.g., multiple choice

                    5 + 5 = ?

    [ans1]      [ans2]      [ans3]      [ans3]

    In which case we may need to make multiple problem objects of different problem types, and this class wraps them all
    """
    def __init__(self, range_ = None, op_ = None, dtype_: str = None, seed = None, q_type_="standard"):
        self.range = range_
        self.q_type = q_type_
        self.op = op_
        self.dtype = dtype_
        self.generator = Generator(range_=self.range, dtype_=self.dtype, seed=seed)
        self.answer = None      # Note: In future a question may have multiple problems associated with it.
                                #       E.g: 4 problems generated for multiple choice question.
                                #       We then randomly select problem 3
                                #       thus self.answer = self.Problem[2].answer, for example.
                                #       For now, we only have one problem per question
                                #       But keep this so that at least Question.answer checks never needs to be modified..

        self.Problem = None #

        self.problem_start_time = datetime.now(timezone.utc)
        self.problem_start_perf_counter = time.perf_counter()
    def prepare(self, problem_id):
        if self.q_type != "standard":
            raise ValueError(f"Only question_type {self.q_type} is currently supported")
        """Generate a problem instance and compute its answer."""

        left, right = self.generator.generate()
        components = ProblemComponents(left=left, right=right, op=self.op)
        self.Problem = make_problem(components, self.dtype)
        self.Problem.id = problem_id

    def info(self):
        return to_dict(self)

    def snapshot(self, last_event):
        """
        Create a snapshot of this Question instance.
        """
        left, right = self.Problem.components.left, self.Problem.components.right

        data = {
            "problem_id": self.Problem.id,
            "problem_type": f"{self.op}_{self.dtype}",
            "created_at": str(self.problem_start_time),
            "left_operand": left,
            "right_operand": right,
            "answer": self.answer,
            "status": "unanswered",
            "event": last_event
        }
        if last_event == "user_answer_validated":
            data["answer_ms"] = self.time_elapsed_ms()
            data["is_correct"] = True

        if last_event in ["user_answer_validated", "game_timed_out", "user_pressed_end_game"]:

            data["mod_log"] = self.Problem.mod_log

            terms = ["left", "right", "ans"]
            # The "effective" problem is just stored as the normal problem, i.e,
            # left_tags = self.Problem.eff_tag_info["terms"]["left"]["tags"]
            # But for the "base" problem it will be
            # base_left_tags = self.Problem.base_tag_info["terms"]["left"]["tags"]
            for suffix in ["tags", "features"]:
                for prefix, tag_info in (("base_", self.Problem.base_tag_info), ("", self.Problem.eff_tag_info)):

                    for term in terms:
                        data[f"{prefix}{term}_{suffix}"] = tag_info["terms"][f"{term}"][f"{suffix}"]

                    data[f"{prefix}operator_{suffix}"] = tag_info["operator"][f"{suffix}"]
                    data[f"{prefix}general_{suffix}"] = tag_info["general"][f"{suffix}"]


        return data

    def render_details(self):
        if self.q_type != "standard":
            raise ValueError(f"Only question_type {self.q_type} is currently supported")


        return self.Problem.render_details(eff=True)


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