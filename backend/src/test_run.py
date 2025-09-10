import uuid
from src.models.player import Player
from src.services.game import play_hand

players = [Player(i) for i in range(1, 7)]

for hand_num in range(3):
    hand = play_hand(players, dealer_index=hand_num)
    print(f"\n--- Hand {hand_num+1} ---")
    print("UUID:", hand.id)
    print(hand.mainInfo)
    print(hand.dealt)
    print(hand.actions)
    print(hand.result)