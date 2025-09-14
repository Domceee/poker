from typing import List, Optional
from src.models import hand
from src.models.hand import HandHistory
from src.db import get_db_connection

class HandRepository:

    @staticmethod
    def save_hand(hand: HandHistory):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO hands (id, stack, hands, actions, result) VALUES (%s, %s, %s, %s, %s)",
                    (hand.id, hand.mainInfo, hand.dealt, hand.actions, hand.result)
                )
                conn.commit()
    
    @staticmethod
    def get(hand_id: str):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, stack, hands, actions, result FROM hands WHERE id = %s", (hand_id,))
                row = cur.fetchone()
                if row:
                    return HandHistory(
                        id=str(row[0]),
                        mainInfo=row[1],
                        dealt=row[2],
                        actions=row[3],
                        result=row[4]
                    )
                return None 
            
    @staticmethod
    def list_all():
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, stack, hands, actions, result FROM hands")
                rows = cur.fetchall()
                hands = []
                for row in rows:
                    hand = HandHistory(
                        id=str(row[0]),
                        mainInfo=row[1],
                        dealt=row[2], 
                        actions=row[3],
                        result=row[4]
                    )
                    hands.append(hand)
                return hands
