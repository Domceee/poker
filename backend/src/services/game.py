from pokerkit import Automation, NoLimitTexasHoldem
import uuid
from src.models.hand import HandHistory
from src.models.player import Player
import random

def play_hand(user_actions: list[str]) -> HandHistory:
    hand_id = str(uuid.uuid4())
    players = [Player.create() for _ in range(6)]
    stacks = tuple([10000 for _ in players])

    state = NoLimitTexasHoldem.create_state(
        (
            Automation.ANTE_POSTING,
            Automation.BET_COLLECTION,
            Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
            Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING,
            Automation.CHIPS_PULLING,
        ),
        False,
        0,
        (20, 40),
        40,
        stacks,
        len(players),
    )

    # dealer = players[dealer_index % len(players)]
    # small_blind = players[(dealer_index + 1) % len(players)]
    # big_blind = players[(dealer_index + 2) % len(players)]

    hole_cards = {}
    for p in players:
        hole_cards[p.id] = str(state.deal_hole())

    #dealt_str = "\n".join([f"Player {i} ({player.id}): {cards}" for i, (player, cards) in enumerate(zip(players, hole_cards.values()))])
    dealt_str = "\n".join([f"{pid}: {cards}" for pid, cards in hole_cards.items()])

    actions = []
    actions_index = 0

    while state.status == "RUNNING":
        if state.actor_indices:
            current_player_index = state.actor_indices[0]

            # Logic made for the user
            if current_player_index == 0:
                if actions_index < len(user_actions):
                    act = user_actions[actions_index]
                    actions_index += 1

                    if act == "f":
                        state.fold()
                        actions.append("User folds")
                    elif act == "c":
                        state.check_or_call()
                        actions.append("User calls")
                    elif act.startswith("r"):
                        amount = int(act.split()[1])
                        state.complete_bet_or_raise_to(amount)
                        actions.append(f"User raises to ${amount}")
                    else:
                        state.check_or_call()
                        actions.append("User checks")
                else:
                    state.check_or_call()
                    actions.append("User checks (default)")

            # Logic made for bots
            else:
                if state.can_check_or_call():
                    if random.random() < 0.7:
                        state.check_or_call()
                        actions.append(f"Player {current_player_index} calls")
                    else:
                        state.fold()
                        actions.append(f"Player {current_player_index} folds")
                elif state.can_fold():
                    state.fold()
                    actions.append(f"Player {current_player_index} folds")
        
        else:
            if state.can_burn_card():
                state.burn_card()
            elif state.can_deal_board():
                state.deal_board()
            else:
                break

    # actions_str = "\n".join(actions)

    # main_info = f"Stack {stacks}, Dealer: {dealer}, Blinds: {small_blind}/{big_blind}"

    # winnings = []
    # for i, player in enumerate(players):
    #     net = state.stacks[i] - stacks[i]
    #     sign = "+" if net >= 0 else ""
    #     winnings.append(f"Player {i} ({player.id}): {sign}${abs(net)}")
    # result_str = "\n".join(winnings)

    result_lines = []
    for i, p in enumerate(players):
        net = state.stacks[i] - stacks[i]
        sign = "+" if net >= 0 else ""
        result_lines.append(f"Player {i} ({p.id}): {sign}{net}")
    result_str = "\n".join(result_lines)

    main_info = f"Stacks: {stacks}, Blinds: {state.small_blind}/{state.big_blind}"

    return HandHistory(
        id = hand_id,
        mainInfo = main_info,
        dealt = dealt_str,
        actions = "\n".join(actions),
        result = result_str
    )