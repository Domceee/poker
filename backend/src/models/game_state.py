from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.models.player import Player
import uuid

@dataclass
class GameState:
    id: str
    players: List[Player]
    dealer_index: int
    stacks: List[int]
    poker_state: Any
    board: List[str] = field(default_factory=list)
    hole_cards: Dict[int, str] = field(default_factory=dict)
    actions_log: List[str] = field(default_factory=list)
    status: str = "RUNNING"