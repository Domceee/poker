from dataclasses import dataclass
from typing import List
from src.models.player import Player

@dataclass
class GameState:
    id: str
    players: List[Player]
    stacks: List[int]
    pot: int
    board: List[str]
    current_player: int
    actions: List[str]
    status: str