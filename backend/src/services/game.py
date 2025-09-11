from pokerkit import Automation, NoLimitTexasHoldem
import uuid
from src.models.hand import HandHistory
from src.models.player import Player
from src.models.game_state import GameState
import random

def play_hand(user_actions: list[str] = None) -> HandHistory:

    if user_actions is None:
        user_actions = []

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

    # Main information that will be registered in the database
    hand_id = f"Hand #{str(uuid.uuid4())}"
    # Format: "Stack 10000; Dealer: Player 3; Player 4 Small blind; Player 6 Big blind"
    main_info = ""
    # Format: "Hands: Player1: Tc2c; Player2: 5d4c; Player 3: Ah4s; Player 4: QcTd; Player 5: Qh4d; Player 6: Ks5s"
    dealt_str = ""
    # Format: "Actions: f:f:f:r300:c:f 3hKdQs x:b100:c Ac x:x Th b80:r160:c"
    actions = []
    # Format: "Winnings: Player 1: -40; Player 2: 0; Player 3: -560; Player 4: +850; Player 5: -200; Player 6: -50"
    result_str = ""

    #---------------------------------------------Dealer, Small Blind, Big Blind---------------------------------------------

    dealer_index = 2
    dealer = f"Player {dealer_index + 1}"
    small_blind = f"Player {(dealer_index + 1) % 6 + 1}"
    big_blind = f"Player {(dealer_index + 3) % 6 + 1}"
    main_info = f"Stack 10000; Dealer: {dealer}; {small_blind} Small blind; {big_blind} Big blind"

    #------------------------------------------------------------------------------------------------------------------------

    #------------------------------------------------------Hand deals--------------------------------------------------------
    hole_cards = {}
    first_cards = []
    second_cards = []
    
    for p in players:
        first_cards.append(state.deal_hole())
    for p in players:
        second_cards.append(state.deal_hole())

    for i, p in enumerate(players):
        card1 = first_cards[i]
        card2 = second_cards[i]
        hole_cards[p.id] = f"{card1}, {card2}"

    dealt_str = "Hands: " + "; ".join([
        f"Player{i+1}: {str(first_cards[i].cards[0])}{str(second_cards[i].cards[0])}"
        for i in range(6)
    ])
    #-------------------------------------------------------------------------------------------------------------------------

    #-------------------------------------------------------Gameplay----------------------------------------------------------

    street_names = ["Pre-flop", "Flop", "Turn", "River"]
    actions_index = 0

    while state.status:
        # Handle player actions
        if state.actor_indices:
            current_player_index = state.actor_indices[0]
            current_player = players[current_player_index]
            
            # Get current street info
            current_street = getattr(state, 'street_index', 0)
            street_name = street_names[min(current_street, len(street_names)-1)]
            
            # Get betting information
            can_check = state.checking_or_calling_amount == 0
            call_amount = state.checking_or_calling_amount or 0
            current_stack = state.stacks[current_player_index]

            # User logic (Player 0)
            if current_player_index == 0:
                if actions_index < len(user_actions):
                    action = user_actions[actions_index].strip().lower()
                    actions_index += 1
                    
                    if action == "f":
                        state.fold()
                        actions.append(f"{street_name}: User folds")
                        
                    elif action == "c":
                        state.check_or_call()
                        if can_check:
                            actions.append(f"{street_name}: User checks")
                        else:
                            actions.append(f"{street_name}: User calls ${call_amount}")
                            
                    elif action.startswith("r"):
                        try:
                            parts = action.split()
                            if len(parts) >= 2:
                                raise_amount = int(parts[1])
                                if raise_amount <= current_stack:
                                    state.complete_bet_or_raise_to(raise_amount)
                                    actions.append(f"{street_name}: User raises to ${raise_amount}")
                                else:
                                    # All-in if raise amount exceeds stack
                                    state.complete_bet_or_raise_to(current_stack)
                                    actions.append(f"{street_name}: User goes all-in for ${current_stack}")
                            else:
                                # Invalid raise format, default to call/check
                                state.check_or_call()
                                action_desc = "checks" if can_check else f"calls ${call_amount}"
                                actions.append(f"{street_name}: User {action_desc} (invalid raise)")
                        except (ValueError, IndexError):
                            # Invalid raise amount, default to call/check
                            state.check_or_call()
                            action_desc = "checks" if can_check else f"calls ${call_amount}"
                            actions.append(f"{street_name}: User {action_desc} (invalid raise)")
                    else:
                        # Unknown action, default to check/call
                        state.check_or_call()
                        action_desc = "checks" if can_check else f"calls ${call_amount}"
                        actions.append(f"{street_name}: User {action_desc} (unknown action)")
                else:
                    # No more user actions, default behavior
                    state.check_or_call()
                    action_desc = "checks" if can_check else f"calls ${call_amount}"
                    actions.append(f"{street_name}: User {action_desc} (auto)")

            # Bot logic (Players 1-5)
            else:
                # Improved bot decision making
                if can_check:
                    # Can check for free
                    action_weights = [0.6, 0.25, 0.15]  # [check, bet_small, bet_large]
                    action = random.choices(['check', 'bet_small', 'bet_large'], 
                                          weights=action_weights)[0]
                    
                    if action == 'check':
                        state.check_or_call()
                        actions.append(f"{street_name}: Player {current_player_index} checks")
                        
                    elif action == 'bet_small':
                        bet_size = min(call_amount + 40, current_stack)  # Small bet
                        if bet_size > call_amount:
                            state.complete_bet_or_raise_to(bet_size)
                            actions.append(f"{street_name}: Player {current_player_index} bets ${bet_size}")
                        else:
                            state.check_or_call()
                            actions.append(f"{street_name}: Player {current_player_index} checks")
                            
                    else:  # bet_large
                        bet_size = min(call_amount + 120, current_stack)  # Large bet
                        if bet_size > call_amount:
                            state.complete_bet_or_raise_to(bet_size)
                            actions.append(f"{street_name}: Player {current_player_index} bets ${bet_size}")
                        else:
                            state.check_or_call()
                            actions.append(f"{street_name}: Player {current_player_index} checks")
                
                else:
                    # Must call or fold
                    call_ratio = call_amount / current_stack if current_stack > 0 else 1
                    
                    # Adjust fold probability based on call amount relative to stack
                    if call_ratio > 0.5:  # Large bet relative to stack
                        fold_prob = 0.8
                    elif call_ratio > 0.2:  # Medium bet
                        fold_prob = 0.5
                    else:  # Small bet
                        fold_prob = 0.3
                    
                    if random.random() < fold_prob:
                        state.fold()
                        actions.append(f"{street_name}: Player {current_player_index} folds")
                    else:
                        # Decide between call and raise
                        if random.random() < 0.8:  # 80% call, 20% raise
                            state.check_or_call()
                            actions.append(f"{street_name}: Player {current_player_index} calls ${call_amount}")
                        else:
                            # Raise
                            raise_size = min(call_amount * 2.5, current_stack)
                            if raise_size > call_amount:
                                state.complete_bet_or_raise_to(int(raise_size))
                                actions.append(f"{street_name}: Player {current_player_index} raises to ${int(raise_size)}")
                            else:
                                state.check_or_call()
                                actions.append(f"{street_name}: Player {current_player_index} calls ${call_amount}")
        
        else:
            # Handle card dealing and burning
            if state.can_burn_card():
                state.burn_card()
                
            elif state.can_deal_board():
                state.deal_board()
                if hasattr(state, 'board_cards') and state.board_cards:
                    board = list(state.board_cards)
                        
            else:
                break

    #-------------------------------------------------------------------------------------------------------------------------

    #-------------------------------------------------------Results-----------------------------------------------------------

    result_lines = []
    for i, p in enumerate(players):
        net = state.stacks[i] - stacks[i]
        sign = "+" if net >= 0 else ""
        result_lines.append(f"Player {i}: {sign}{net}")
    result_str = "; ".join(result_lines)

    #-------------------------------------------------------------------------------------------------------------------------

    # Hand History after the game
    return HandHistory(
        id = hand_id,
        mainInfo = main_info,
        dealt = dealt_str,
        actions = str(actions),
        result = result_str
    )
