from dataclasses import dataclass
from typing import List
import uuid

@dataclass
class HandHistory:
    id: str
    mainInfo: str
    dealt: str
    actions: str
    result: str

@classmethod
def create(cls, mainInfo: str, dealt: str, actions: str, result: str) -> 'HandHistory':
    return cls(
        id=str(uuid.uuid4()),
        mainInfo=mainInfo,
        dealt=dealt,
        actions=actions,
        result=result
    )
