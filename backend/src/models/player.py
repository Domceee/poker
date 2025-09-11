from dataclasses import dataclass
import uuid

@dataclass
class Player:
    id: int

    @classmethod
    def create(cls, is_user: bool = False):
        return cls(id=str(uuid.uuid4()))
