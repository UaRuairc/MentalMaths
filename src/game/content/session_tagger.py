from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.gameplay.game_controller import Game


class TagData(TypedDict):
    terms: dict
    operator: dict
    general: dict

def update_session_tags(g: "Game", t: TagData):

    """
    Update game session tags using TagData.
    """

    terms = ["left", "right", "ans"]

    for term in terms:
        g.tags.setdefault(term, set()).update(t["terms"][term]["tags"])

    g.tags.setdefault("operator", set()).update(t["operator"].get("tags", set()))
    g.tags.setdefault("general", set()).update(t["general"].get("tags", set()))