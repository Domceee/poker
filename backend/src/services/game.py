from pokerkit import Automation, NoLimitTexasHoldem
import uuid
from src.models.hand import HandHistory
from src.models.player import Player
from src.models.game_state import GameState
from src.repositories.hand_repo import HandRepository
import random
from typing import Optional

_CURRENT_GAME: Optional[GameState] = None

big_blind = 40
small_blind = 20
starting_stack = 10000

# ----------------------------------------Create initial poker state ------------------------------
def create_state(num_players: int):
    stacks = tuple([starting_stack for _ in range(num_players)])
    return NoLimitTexasHoldem.create_state(
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
        (small_blind, big_blind),
        big_blind,
        stacks,
        num_players,
    )
#----------------------------------------------------------------------------------------------------

# ---------------------------------------- Starting hands dealt -------------------------------------
def start_hand(num_players: int = 6, dealer_index: int = 0) -> GameState:
    global _CURRENT_GAME
    if _CURRENT_GAME is not None:
        raise Exception("A game is already in progress")

    players = [Player.create(i+1) for i in range(num_players)]
    poker_state = create_state(num_players)

    dealer = f"Player {dealer_index + 1}"
    sb = f"Player {(dealer_index + 1) % num_players + 1}"
    bb = f"Player {(dealer_index + 2) % num_players + 1}"

    hole_cards = {}
    first_card = []
    second_card = []
    for i in range(num_players):
        # cards = poker_state.deal_hole()
        # hole_cards[i + 1] = str(cards)
        first_card.append(poker_state.deal_hole())
    for i in range(num_players):
        second_card.append(poker_state.deal_hole())

    for i, p in enumerate(players):
        card1 = first_card[i]
        card2 = second_card[i]
        hole_cards[p.seat] = f"{card1}, {card2}"

    game_id = str(uuid.uuid4())
    gs = GameState(
        id=game_id,
        players=players,
        dealer_index=dealer_index,
        stacks=[starting_stack for _ in players],
        poker_state=poker_state,
        hole_cards=hole_cards,
        actions_log=[],
        board=[],
        status="RUNNING",
    )
    _CURRENT_GAME = gs

    for i, cards in hole_cards.items():
        gs.actions_log.append(f"Player {i} is dealt {str(first_card[i-1].cards[0])}, {str(second_card[i-1].cards[0])}")

    gs.actions_log.append("---")
    gs.actions_log.append(f"{dealer} is the dealer")
    gs.actions_log.append(f"{sb} posts small blind - {small_blind} chips")
    gs.actions_log.append(f"{bb} posts big blind - {big_blind} chips")
    gs.actions_log.append("---")

    return gs
# --------------------------------------------------------------------------------------------------------

# ---------------------------------------- Get current game state ----------------------------------------
def get_state() -> Optional[GameState]:
    return _CURRENT_GAME

def reset_game(stack_amount: int = None) -> None:
    global _CURRENT_GAME, starting_stack
    _CURRENT_GAME = None
    
    if stack_amount is not None:
        starting_stack = stack_amount
        print(f"DEBUG: Global starting_stack reset to {starting_stack}")

def active_game() -> bool:
    return _CURRENT_GAME is not None

def append_board_token(gs: GameState):
    state = gs.poker_state
    if hasattr(state, "board_cards") and state.board_cards:
        token = "".join(str(c) for c in state.board_cards)
        gs.actions_log.append(token)
        gs.board = [str(c) for c in state.board_cards]

def actor_indices(state):
    return getattr(state, "actor_indices", None)

def get_check_call_amount(state) -> int:
    return getattr(state, "checking_or_calling_amount", 0) or 0

def update_stacks(gs: GameState):
    """Update GameState stacks from poker_state"""
    if hasattr(gs.poker_state, 'stacks'):
        gs.stacks = list(gs.poker_state.stacks)

def apply_stacks_to_players(stack_amount: int) -> GameState:
    global _CURRENT_GAME, starting_stack
    starting_stack = stack_amount

    if _CURRENT_GAME is not None:
        _CURRENT_GAME.stacks = [stack_amount for _ in _CURRENT_GAME.players]
#----------------------------------------------------------------------------------------------------------

#---------------------------------------- Bot actions until user turn -------------------------------------
def bots_act_until_user_turn(gs: GameState):
    state = gs.poker_state

    while actor_indices(state):
        current_index = state.actor_indices[0]
        if current_index == 0:  # User's turn
            break

        try:
            call_amount = get_check_call_amount(state)
            
            if state.can_check_or_call():
                if call_amount == 0:
                    # No bet to call - decide whether to check or bet
                    decision = random.random()
                    if decision < 0.6:  # 60% chance to check
                        state.check_or_call()
                        gs.actions_log.append(f"Player {current_index + 1} checks")
                    elif state.can_complete_bet_or_raise_to():  # 40% chance to bet
                        bet_amt = min(big_blind * random.randint(2, 4), state.stacks[current_index])
                        state.complete_bet_or_raise_to(bet_amt)
                        gs.actions_log.append(f"Player {current_index + 1} bets {bet_amt} chips")
                    else:
                        state.check_or_call()
                        gs.actions_log.append(f"Player {current_index + 1} checks")
                else:
                    # There's a bet to call - decide call/raise/fold based on amount
                    decision = random.random()
                    pot_odds = call_amount / max(call_amount, big_blind)
                    
                    if call_amount > big_blind * 5:  # Large bet - more likely to fold
                        if decision < 0.6:
                            state.fold()
                            gs.actions_log.append(f"Player {current_index + 1} folds")
                        else:
                            state.check_or_call()
                            gs.actions_log.append(f"Player {current_index + 1} calls {call_amount} chips")
                    elif decision < 0.7:  # Normal bet - likely to call
                        state.check_or_call()
                        gs.actions_log.append(f"Player {current_index + 1} calls {call_amount} chips")
                    elif decision < 0.85 and state.can_complete_bet_or_raise_to():  # Sometimes raise
                        raise_amt = min(call_amount * 2, state.stacks[current_index])
                        state.complete_bet_or_raise_to(raise_amt)
                        gs.actions_log.append(f"Player {current_index + 1} raises to {raise_amt} chips")
                    else:  # Sometimes fold
                        state.fold()
                        gs.actions_log.append(f"Player {current_index + 1} folds")
                        
            elif state.can_fold():
                state.fold()
                gs.actions_log.append(f"Player {current_index + 1} folds")
            else:
                print(f"DEBUG: Bot {current_index + 1} has no valid actions")
                break
                
        except Exception as e:
            print(f"DEBUG: Bot {current_index + 1} action failed: {e}")
            # Safe fallback
            try:
                if state.can_fold():
                    state.fold()
                    gs.actions_log.append(f"Player {current_index + 1} folds")
                elif state.can_check_or_call():
                    state.check_or_call()
                    call_amount = get_check_call_amount(state)
                    action_name = "checks" if call_amount == 0 else f"calls {call_amount} chips"
                    gs.actions_log.append(f"Player {current_index + 1} {action_name}")
                else:
                    break
            except Exception:
                break

        update_stacks(gs)

        # Check if round ended - deal next street if possible
        if not actor_indices(state):
            if getattr(state, "can_burn_card", False) and state.can_burn_card():
                state.burn_card()
            if getattr(state, "can_deal_board", False) and state.can_deal_board():
                state.deal_board()
                append_board_token(gs)

    return gs
#----------------------------------------------------------------------------------------------------------

# ---------------------------------------- Apply user action ----------------------------------------------
def apply_action(game_id: str, action_token: str, amount: int | None = None) -> GameState:
    global _CURRENT_GAME

    gs = _CURRENT_GAME
    if gs is None:
        raise KeyError("Game not found")

    state = gs.poker_state

    if actor_indices(state) and state.actor_indices[0] != 0:
        bots_act_until_user_turn(gs)

    if actor_indices(state) and state.actor_indices[0] == 0:
        tok = action_token.strip().lower()
        try:
            if tok == "f" and state.can_fold():
                state.fold()
                gs.actions_log.append("Player 1 folds")
                
            elif tok == "x":
                call_amount = get_check_call_amount(state)
                if call_amount == 0 and state.can_check_or_call():
                    state.check_or_call()
                    gs.actions_log.append("Player 1 checks")
                else:
                    raise Exception(f"Cannot check - must call {call_amount} or fold")
                    
            elif tok == "c":
                call_amount = get_check_call_amount(state)
                if call_amount > 0 and state.can_check_or_call():
                    state.check_or_call()
                    gs.actions_log.append(f"Player 1 calls {call_amount} chips")
                else:
                    raise Exception("No bet to call - use check instead")
                    
            elif tok == "b":
                print(f"DEBUG: Attempting to bet {amount}")
                print(f"DEBUG: Can complete bet: {state.can_complete_bet_or_raise_to()}")
                print(f"DEBUG: Current stack: {state.stacks[0]}")
                
                # FIX: Check call_amount, not amount
                call_amount = get_check_call_amount(state)
                print(f"DEBUG: Call amount: {call_amount}")
                
                if call_amount > 0:
                    raise Exception(f"Cannot bet - there's already a bet of {call_amount} to call")
                
                if amount and state.can_complete_bet_or_raise_to() and amount <= state.stacks[0] and amount >= big_blind:
                    state.complete_bet_or_raise_to(amount)
                    gs.actions_log.append(f"Player 1 bets {amount} chips")
                    print(f"DEBUG: Bet successful")
                else:
                    print(f"DEBUG: Cannot bet - insufficient stack or below minimum")
                    raise Exception("Cannot bet - invalid amount or insufficient stack")
                    
            elif tok == "r":
                print(f"DEBUG: Attempting to raise to {amount}")
                
                # Can only raise if there's an existing bet
                call_amount = get_check_call_amount(state)
                if call_amount == 0:
                    raise Exception("Cannot raise - no bet to raise")
                
                min_raise = call_amount * 2
                if amount and state.can_complete_bet_or_raise_to() and amount <= state.stacks[0] and amount >= min_raise:
                    state.complete_bet_or_raise_to(amount)
                    gs.actions_log.append(f"Player 1 raises to {amount} chips")
                    print(f"DEBUG: Raise successful")
                else:
                    print(f"DEBUG: Cannot raise - insufficient stack or below minimum raise")
                    raise Exception(f"Cannot raise - minimum raise is {min_raise}")
                    
            elif tok == "allin":
                # All-in logic
                player_stack = state.stacks[0]
                print(f"DEBUG: Attempting all-in with stack {player_stack}")
                
                if state.can_complete_bet_or_raise_to() and player_stack > 0:
                    state.complete_bet_or_raise_to(player_stack)
                    gs.actions_log.append("Player 1 goes all-in")
                    print(f"DEBUG: All-in successful")
                else:
                    print(f"DEBUG: Cannot go all-in")
                    raise Exception("Cannot go all-in")
            else:
                # Default action - try to check/call appropriately
                call_amount = get_check_call_amount(state)
                if state.can_check_or_call():
                    state.check_or_call()
                    action_name = "checks" if call_amount == 0 else f"calls {call_amount} chips"
                    gs.actions_log.append(f"Player 1 {action_name}")
                else:
                    raise Exception("No valid action available")
                    
        except Exception as e:
            print(f"DEBUG: Exception in user action: {e}")
            # Re-raise the exception so the API can handle it properly
            raise e

    update_stacks(gs)
    
    # Continue with bot actions
    bots_act_until_user_turn(gs)

    # Handle board dealing between rounds
    if not actor_indices(state):
        if getattr(state, "can_burn_card", False) and state.can_burn_card():
            state.burn_card()
        if getattr(state, "can_deal_board", False) and state.can_deal_board():
            state.deal_board()
            append_board_token(gs)

    # Check for game end
    finished_flag = False
    
    # Check PokerKit status
    status_value = getattr(state, "status", None)
    if status_value is not None:
        status_str = str(status_value).upper()
        if "FINISHED" in status_str or "COMPLETE" in status_str:
            finished_flag = True
            print(f"DEBUG: Game finished via status: {status_value}")

    # Check if no more actions and no more cards to deal
    if not finished_flag and not actor_indices(state):
        can_deal_more = (getattr(state, "can_burn_card", False) and state.can_burn_card()) or \
                       (getattr(state, "can_deal_board", False) and state.can_deal_board())
        if not can_deal_more:
            finished_flag = True
            print(f"DEBUG: Game finished - no more actions or cards")

    print(f"DEBUG: Finished flag final value: {finished_flag}")
    if finished_flag:
        print("DEBUG: About to call finalize_hand()")
        finalize_hand(gs)

    return gs
#-----------------------------------------------------------------------------------------------------------------

# ---------------------------------------- Finalize hand and persist history -------------------------------------
def finalize_hand(gs: GameState) -> HandHistory:
    global _CURRENT_GAME
    state = gs.poker_state

    hands_entries = []
    for seat in range(1, len(gs.players) + 1):
        hc = gs.hole_cards.get(seat, "")
        clean_cards = hc.replace(", ", "").replace(" ", "")
        hands_entries.append(f"Player{seat}: {clean_cards}")
    dealt_str = "Hands: " + "; ".join(hands_entries)

    actions_str = " ".join(gs.actions_log)

    update_stacks(gs)
    final_stacks = gs.stacks if hasattr(gs, 'stacks') else gs.poker_state.stacks

    winnings_parts = []
    for i in range(len(gs.players)):
        start = starting_stack
        final = final_stacks[i]
        net = final - start
        sign = "+" if net > 0 else ""
        winnings_parts.append(f"Player {i+1}: {sign}{net}")

    result_str = "Winnings: " + "; ".join(winnings_parts)

    dealer = f"Player {gs.dealer_index + 1}"
    small_blind_player = f"Player {(gs.dealer_index + 1) % len(gs.players) + 1}"
    big_blind_player = f"Player {(gs.dealer_index + 2) % len(gs.players) + 1}"
    main_info = f"Stack {starting_stack}; Dealer: {dealer}; {small_blind_player} Small blind; {big_blind_player} Big blind"

    hand = HandHistory(
        id=gs.id, 
        mainInfo=main_info, 
        dealt=dealt_str, 
        actions=actions_str, 
        result=result_str
    )

    try:
        HandRepository.save_hand(hand)
        print(f"DEBUG: Hand {gs.id} saved to database")
    except Exception as e:
        print(f"DEBUG: Failed to save hand to database: {e}")

    _CURRENT_GAME = None
    gs.status = "FINISHED"

    return hand