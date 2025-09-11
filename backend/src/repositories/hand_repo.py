from typing import List, Optional
from src.models.hand import HandHistory
from src.db import get_db_connection

class HandRepository:
    
    @staticmethod
    def save_hand(hand: HandHistory):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO hands (id, stack, hands, actions, result)
                    VALUES (%s, %s, %s, %s, %s)
                """, (hand.id, hand.mainInfo, hand.dealt, hand.actions, hand.result))
            conn.commit()

    @staticmethod
    def get_hand(hand_id: str) -> Optional[HandHistory]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, stack, hands, actions, result FROM hands WHERE id = %s", (hand_id,))
                rows = cur.fetchall()
                if rows:
                    return HandHistory(id=rows[0], mainInfo=rows[1], dealt=rows[2], actions=rows[3], result=rows[4])
        return None