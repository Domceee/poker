from dataclasses import dataclass
import uuid

@dataclass
class Player:
    seat: int

    @classmethod
    def create(cls, seat: int) -> 'Player':
        return cls(seat=seat)

    @staticmethod
    def default():
        return [Player(i+1) for i in range(6)]
    
    def __str__(self) -> str:
        return f"Player {self.seat}"