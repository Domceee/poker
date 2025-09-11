from dataclasses import dataclass
import uuid

@dataclass
class Player:
    id: int
    stack: int = 10000
    is_user: bool = False

    @classmethod
    def create(cls, is_user: bool = False):
        return cls(id=str(uuid.uuid4()), is_user=is_user)
