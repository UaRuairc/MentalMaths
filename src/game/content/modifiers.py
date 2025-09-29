from dataclasses import dataclass, replace
from typing import ClassVar, Optional
from src.config.config_management import ConfigManager as cm
from collections.abc import Iterable
from abc import ABC
from datetime import datetime, timezone
from copy import deepcopy


class Modifier(ABC):


    """
    Abstract base class that serves as a blueprint for defining a mod and, importantly, how a mod behaves for a given target.

    Each mod can be extended to be applied to any object, as long as the corresponding method is defined.

    Attributes:
        id (str): Identifier for the modifier, unique for each modifier instance.
        mod_origin (str): Indicates the origin of the mod, thus the single source of truth of its enabled status.
        widget_name (Optional[str]): Name of the widget, if the modification originates
            from a widget.
        widget_category (Optional[str]): Category of the widget, if applicable.

    Methods:
        modify(target, payload):
            Modifies the target according to the payload by using a handler specific to
            the target's type. Logs updates if modifications occur.

        is_enabled():
            Determines whether the modifier is enabled and can be used for modification.

        get_handler(target):
            Retrieves the handler method for performing a modification, based on the
            type of the provided target.
    """

    #priority: int
    id: ClassVar[str] = ""
    mod_origin: ClassVar[str] = "" # maybe it comes from a widget, or maybe it doesn't
    widget_name: ClassVar[Optional[str]]= None
    widget_category: ClassVar[Optional[str]] = None
    override: ClassVar[Optional[bool]] = None

    def modify(self, target, payload):
        for cls in type(target).__mro__:
            fn = getattr(self, f"_modify_{cls.__name__.lower()}", None)
            if fn:
                return fn(target, payload)

        return None

    def _modify_game(self, g, payload): pass

    def _update_game_mod_history(self, g, payload):
        g.mod_history.setdefault(self.id, [])
        g.mod_history[self.id].append(payload)

    def _modify_problem(self, p, payload): pass

    def _update_problem_mod_history(self, p, payload):
        p.mod_history.setdefault(self.id, [])
        p.mod_history[self.id].append(payload)

    def is_enabled(self):
        pass

class PosOnly(Modifier):

    id = "pos_answers_only"
    mod_origin = "widget"
    description = "Only positive answers are allowed."
    widget_name = "pos_answers_only"
    widget_category = "checkbox"

    def _modify_problem(self, p, payload):
        was_modified = False
        if payload["event"] not in ["new_problem_created", "initial_problem_created"]:
            return


        if p.components.op not in ["add", "sub", "mult", "div"]:
            raise NotImplementedError(f"Operator {p.op} not implemented for pos_only modifier.")

        # p.left and p.right are always positive
        # this is because the choice of problem_type already provides access to all question types, modulo irrelevant signage.

        old_eff_components = replace(p._eff_components)
        if p.components.op == "sub":
            old_left = p.components.left
            new_left = max(p.components.left, p.components.right)
            new_right = min(p.components.left, p.components.right)
            if old_left == new_left:
                was_modified = False
            else:
                p._eff_components = replace(p._eff_components, left=new_left, right=new_right)
                was_modified = True

        payload_update = {
            "was_modified": was_modified,
            "prev_components":  old_eff_components if was_modified else None
        }

        payload.update(payload_update)

        self._update_problem_mod_history(p, payload)
        return

    def is_enabled(self):
        return cm.get_widget_value("pos_answers_only", "checkbox")

class Fade(Modifier):
    id = "fade_problem"
    mod_origin = "widget"
    description = "Fade the problem from sight after a set number of seconds."
    widget_name = "fade_problem"
    widget_category = "checkbox"

    def _modify_problem(self, p, payload):

        self._update_problem_mod_history(p, payload)

    def _modify_game(self, g, payload):

        self._update_game_mod_history(g, payload)

    def is_enabled(self):
        return cm.get_widget_value("fade_problem", "checkbox")


MOD_EVENT_SUBSCRIPTIONS = {
    "game_session_started": [],
    "initial_problem_created": ["pos_answers_only"],
    "new_problem_created": ["pos_answers_only"],
    "user_answer_validated": [],
    "user_answer_invalidated": [],
    "modifier_activated": [],
    "game_timed_out": [],
    "user_pressed_end_game": [],
    "button_interaction": ["fade_problem"]
}

MOD_REGISTRY = {
    "pos_answers_only": PosOnly,
    "fade_problem": Fade
}

MOD_PAYLOADS = {
    "pos_answers_only": {
        "event": None,
        "timestamp": None,
        "was_modified": False,
        "prev_state": None,
    },
    "fade_problem": {
        "event": None,
        "timestamp": None,
        "was_modified": True,
        "duration": 1,
    }
}

def build_payload(mod_id: str, event: str, extra: dict | None = None) -> dict:
    template = MOD_PAYLOADS.get(mod_id, {})
    # make a new dict; resolve callables inline (no deepcopy needed)
    payload = {k: (v() if callable(v) else v) for k, v in template.items()}
    # fill timestamp if template left it None
    if payload.get("timestamp") is None:
        payload["timestamp"] = str(datetime.now(timezone.utc))
    payload["event"] = event
    if extra:
        payload.update(extra)
    return payload


MOD_PRIO = {
    "pos_answers_only": 1,
    "fade_problem": 1
}

VALID_MOD_IDS = set(MOD_PRIO)




@dataclass
class ModManager:

    @staticmethod
    def get_subscribed_mod_ids(event):
        return MOD_EVENT_SUBSCRIPTIONS[event]

    @staticmethod
    def get_subscribed_mods(event):
        subscribed_mod_ids = ModManager.get_subscribed_mod_ids(event)
        subscribed_mods =[(inst, build_payload(mod_id, event)) for mod_id in subscribed_mod_ids if (inst := MOD_REGISTRY[mod_id]()).is_enabled()]
        return subscribed_mods

    @staticmethod
    def get_base_mod_payload(mod_id):
        return deepcopy(MOD_PAYLOADS[mod_id])

    @staticmethod
    def validate_ids(mod_ids: str | Iterable[str] | set[str]):

        if mod_ids.issubset(VALID_MOD_IDS):
            return mod_ids, None

        valid = VALID_MOD_IDS.intersection(mod_ids)
        invalid = mod_ids - valid
        return valid, invalid

    @staticmethod
    def order_ids(mod_ids):
        valid_ids, _ = ModManager.validate_ids(mod_ids)
        return sorted(valid_ids, key=lambda m_id: (MOD_PRIO.get(m_id, 1), m_id))

    @staticmethod
    def get_mod_states():

        states = {
            "positive_answers_only": cm.get_widget_value("positive_answers_only", "checkbox"),
            "fade_problem": cm.get_widget_value("fade_problem", "checkbox")
        }

        return states

    @staticmethod
    def mod(event, target):
        subscribed_mods = ModManager.get_subscribed_mods(event)
        for mod, default_payload in subscribed_mods:
            mod.modify(target, default_payload)
