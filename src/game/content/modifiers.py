from dataclasses import dataclass, replace
from typing import ClassVar, Optional
from src.config.config_management import WidgetRegistry 
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

    def modify(self, target, payload) -> bool:
        handler = self.get_handler(target)
        if not handler:
            return False
        log_update = handler(target, payload)

        if log_update is None:
            return False

        self._log(target, log_update)

        return log_update["activated"]

    def _log(self, target, log_update):

        target.mod_log.setdefault("event_history", [])
        target.mod_log.setdefault("mods_activated", [])
        target.mod_log.setdefault("stats", {})
        target.mod_log["stats"].setdefault(self.id, {
            "calls": 0,
            "activations": 0
        })

        target.mod_log["event_history"].append(log_update)
        target.mod_log["stats"][self.id]["calls"] += 1
        if log_update["activated"]:
            target.mod_log["mods_activated"].append(self.id)
            target.mod_log["stats"][self.id]["activations"] += 1



        # log any custom stuff below.
        for cls in type(target).__mro__:
            fn = getattr(self, f"_update_{cls.__name__.lower()}_log", None)
            if fn:
                return fn(target, log_update)

        return None

    def _modify_game(self, g, payload): return payload

    def _update_game_log(self, g, log_update): pass

    def _modify_question(self, q, payload): return payload

    def _update_question_log(self, q, log_update): pass

    def _modify_problem(self, p, payload): return payload

    def _update_problem_log(self, p, log_update): pass

    def is_enabled(self):
        pass

    def get_handler(self, target):
        for cls in type(target).__mro__:
            fn = getattr(self, f"_modify_{cls.__name__.lower()}", None)
            if fn:
                return fn
        return None

class PosOnly(Modifier):

    id = "pos_answers_only"
    mod_origin = "widget"
    description = "Only positive answers are allowed."
    widget_name = "pos_answers_only"
    widget_category = "checkbox"

    def _modify_question(self, q, payload):
        return None

    def _modify_problem(self, p, payload):
        was_modified = False
        log_update = payload
        if payload["event"] not in ["new_question_created", "initial_question_created"]:
            return log_update | {"activated": False, "prev_components": None}
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

        return payload | {
            "activated": was_modified,
            "prev_components":  old_eff_components if was_modified else None
        }

    def is_enabled(self):
        return WidgetRegistry.get_widget_value("pos_answers_only", "checkbox")

class Fade(Modifier):
    id = "fade_problem"
    mod_origin = "widget"
    description = "Fade the problem from sight after a set number of seconds."
    widget_name = "fade_problem"
    widget_category = "checkbox"

    def _modify_question(self, q, payload):
        return None

    def _modify_problem(self, p, payload):

        return payload.copy()

    def _modify_game(self, g, payload):

        return payload.copy()

    def is_enabled(self):
        return WidgetRegistry.get_widget_value("fade_problem", "checkbox")


MOD_EVENT_SUBSCRIPTIONS = {
    "game_session_started": [],
    "initial_question_created": ["pos_answers_only"],
    "new_question_created": ["pos_answers_only"],
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
        "mod_id": "pos_answers_only",
        "event": None,
        "timestamp": None,
        "activated": False,
        "prev_state": None,
    },
    "fade_problem": {
        "mod_id": "fade_problem",
        "event": None,
        "timestamp": None,
        "activated": True,
        "duration": 1,
    }
}

def build_payload(mod_id: str, event: str, extra: dict | None = None) -> dict:
    template = MOD_PAYLOADS.get(mod_id, {})
    payload = {k: (v() if callable(v) else v) for k, v in template.items()}
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
    def get_specific_mods(mod_list, event):
        return [(MOD_REGISTRY[mod_id](), build_payload(mod_id, event)) for mod_id in mod_list]

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
    def mod(event, target, mod_list_override = None):

        seen = set()
        activated = set()

        if mod_list_override is not None:
            mods = ModManager.get_specific_mods(mod_list_override, event)
        else:
            mods = ModManager.get_subscribed_mods(event)

        for mod, default_payload in mods:
            if mod.id in seen:
                continue
            seen.add(mod.id)

            try:
                if mod.modify(target, payload=default_payload):
                    activated.add(mod.id)

            except Exception as e:
                print(f"modifier error: | mod_id:{mod.id} | target:{target} | reason: {e} |")

        return seen, activated, ModManager.get_subtargets(target)

    @staticmethod
    def get_subtargets(target):
        potential_sub_targets = ["Game", "Question", "Problem"]
        cascade_targets = []
        for sub_target in potential_sub_targets:
            attr = getattr(target, sub_target, None)
            if attr is not None:
                cascade_targets.append(attr)
        return cascade_targets

