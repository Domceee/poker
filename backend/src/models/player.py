from dataclasses import dataclass

@dataclass
class Player:
    id: int
    stack: int = 10000