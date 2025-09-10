from pokerkit import Automation, NoLimitTexasHoldem
import uuid
from src.models.hand import HandHistory
from src.models.player import Player

def play_hand(players: list[Player], dealer_index: int) -> HandHistory:
    hand_id = str(uuid.uuid4())
    num_players = len(players)
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
        num_players,
    )

    dealer = players[dealer_index % num_players]
    small_blind = players[(dealer_index + 1) % num_players]
    big_blind = players[(dealer_index + 2) % num_players]

    hole_cards = {}
    for i, player in enumerate(players):
        cards = state.deal_hole()
        hole_cards[player.id] = str(cards)

    dealt_str = "\n".join([f"Player {i} ({player.id}): {cards}" for i, (player, cards) in enumerate(zip(players, hole_cards.values()))])

    actions = []
    while state.status == "RUNNING":
        if state.actor_indices:
            current_player_index = state.actor_indices[0]
            current_player = players[current_player_index]

            if state.can_check_or_call():
                amount = state.checking_or_calling_amount
                if amount == 0:
                    state.check_or_call()
                elif amount <= 100:
                    state.check_or_call()
                    actions.append(f"c")
                else:
                    state.fold()
                    actions.append(f"f")
            elif state.can_fold():
                state.fold()
                actions.append(f"f")
        
        else:
            if state.can_burn_card():
                state.burn_card()
            elif state.can_deal_board():
                board_before = len(state.board_cards) if hasattr(state, 'board_cards') else 0
                state.deal_board()
                board_after = len(state.board_cards) if hasattr(state, 'board_cards') else 0
                
                if board_after == 3 and board_before == 0:
                    flop_cards = ''.join(str(card) for card in state.board_cards[-3:])
                    actions.append(flop_cards)
                elif board_after == 4 and board_before == 3: 
                    turn_card = str(state.board_cards[-1])
                    actions.append(turn_card)
                elif board_after == 5 and board_before == 4:
                    river_card = str(state.board_cards[-1])  
                    actions.append(river_card)
            else:
                break

    actions_str = "\n".join(actions)

    main_info = f"Stack {stacks}, Dealer: {dealer}, Blinds: {small_blind}/{big_blind}"

    winnings = []
    for i, player in enumerate(players):
        net = state.stacks[i] - stacks[i]
        sign = "+" if net >= 0 else ""
        winnings.append(f"Player {i} ({player.id}): {sign}${abs(net)}")
    result_str = "\n".join(winnings)

    return HandHistory(
        id = hand_id,
        mainInfo = main_info,
        dealt = dealt_str,
        actions = actions_str,
        result = result_str
    )