from typing import List, Optional
from src.models.hand import HandHistory

class HandRepository:
    def __init__(self):
        self._hands: List[HandHistory] = []

    def add_hand(self, hand: HandHistory) -> None:
        self._hands.append(hand)
    
    def get_hand(self, hand_id: str) -> Optional[HandHistory]:
        return next((h for h in self._hands if h.id == hand_id), None)
    
    def list_hands(self) -> List[HandHistory]:
        return self._hands