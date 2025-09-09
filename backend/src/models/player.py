from dataclasses import dataclass

@dataclass
class Player:
    id: int
    stack: int
    cards: list[str]