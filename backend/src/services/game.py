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
#----------------------------------------------------------------------------------------------------------

#---------------------------------------- Bot actions until user turn -------------------------------------
def bots_act_until_user_turn(gs: GameState):
    state = gs.poker_state

    while actor_indices(state):
        current_index = state.actor_indices[0]
        if current_index == 0:
            break

        try:
            if getattr(state, "can_check_or_call", False) and state.can_check_or_call():
                amt = get_check_call_amount(state)
                if amt == 0:
                    state.check_or_call()
                    gs.actions_log.append(f"Player {current_index + 1} checks")
                else:
                    decision = random.random()
                    if decision < 0.7 or amt <= big_blind * 2:
                        state.check_or_call()
                        gs.actions_log.append(f"Player {current_index + 1} calls {amt} chips")
                    else:
                        state.fold()
                        gs.actions_log.append(f"Player {current_index + 1} folds")
            elif getattr(state, "can_complete_bet_or_raise_to", False) and state.can_complete_bet_or_raise_to():
                bet_amt = min(big_blind * 2, state.stacks[current_index])
                state.complete_bet_or_raise_to(bet_amt)
                gs.actions_log.append(f"Player {current_index + 1} bets {bet_amt} chips")
            elif getattr(state, "can_fold", False) and state.can_fold():
                state.fold()
                gs.actions_log.append(f"Player {current_index + 1} folds")
            else:
                break
        except Exception:
            try:
                state.fold()
                gs.actions_log.append(f"Player {current_index + 1} folds")
            except Exception:
                break

        update_stacks(gs)

        if not actor_indices(state):
            if getattr(state, "can_burn_card", False) and state.can_burn_card():
                state.burn_card()
            if getattr(state, "can_deal_board", False) and state.can_deal_board():
                state.deal_board()
                append_board_token(gs)

    return gs
#----------------------------------------------------------------------------------------------------------

# ---------------------------------------- Apply user action ----------------------------------------------
def apply_action(game_id: str, action_token: str) -> GameState:
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
            elif tok == "x" and state.can_check_or_call():
                state.check_or_call()
                gs.actions_log.append("Player 1 checks")
            elif tok == "c" and state.can_check_or_call():
                state.check_or_call()
                gs.actions_log.append("Player 1 calls")
            elif tok.startswith("b"):
                amt = int(tok[1:])
                state.complete_bet_or_raise_to(amt)
                gs.actions_log.append(f"Player 1 bets {amt} chips")
                if state.can_complete_bet_or_raise_to() and amt <= state.stacks[0]:
                    state.complete_bet_or_raise_to(amt)
                    print(f"DEBUG: Bet successful")
                else:
                    print(f"DEBUG: Cannot bet - either can't bet or insufficient stack")
                    raise Exception("Cannot bet")
            elif tok.startswith("r"):
                amt = int(tok[1:])
                state.complete_bet_or_raise_to(amt)
                if state.can_complete_bet_or_raise_to() and amt <= state.stacks[0]:
                    state.complete_bet_or_raise_to(amt)
                    gs.actions_log.append(f"Player 1 raises to {amt} chips")
                    print(f"DEBUG: Raise successful")  # ADDED: Debug logging
                else:
                    print(f"DEBUG: Cannot raise")  # ADDED: Debug logging
                    raise Exception("Cannot raise")
            elif tok == "allin":
                player_stack = state.stacks[0]
                if state.can_complete_bet_or_raise_to():
                    state.complete_bet_or_raise_to(player_stack)
                    gs.actions_log.append("Player 1 goes all-in")
                    print(f"DEBUG: All-in successful")  # ADDED: Debug logging
                else:
                    print(f"DEBUG: Cannot go all-in")  # ADDED: Debug logging
                    raise Exception("Cannot go all-in")
            else:
                state.check_or_call()
                token = "x" if get_check_call_amount(state) == 0 else "c"
                gs.actions_log.append(token)
        except Exception:
            try:
                state.fold()
                gs.actions_log.append("f")
            except Exception:
                pass
    
    update_stacks(gs)
    bots_act_until_user_turn(gs)

    if not actor_indices(state):
        if getattr(state, "can_burn_card", False) and state.can_burn_card():
            state.burn_card()
        if getattr(state, "can_deal_board", False) and state.can_deal_board():
            state.deal_board()
            append_board_token(gs)

    finished_flag = False

    status_value = getattr(state, "status", None)
    if status_value is not None:
        if getattr(status_value, "name", None) == "FINISHED" or status_value == "FINISHED":
            finished_flag = True

    if finished_flag:
        finalize_hand(gs)

    return gs
#-----------------------------------------------------------------------------------------------------------------

# ---------------------------------------- Finalize hand and persist history -------------------------------------
def finalize_hand(gs: GameState) -> HandHistory:
    global _CURRENT_GAME
    state = gs.poker_state

    # CHANGED: Updated hand format to match your required format
    hands_entries = []
    for seat in range(1, len(gs.players) + 1):
        hc = gs.hole_cards.get(seat, "")
        # CHANGED: Remove spaces and commas from hole cards format
        clean_cards = hc.replace(", ", "").replace(" ", "")
        hands_entries.append(f"Player{seat}: {clean_cards}")
    dealt_str = "Hands: " + "; ".join(hands_entries)

    # CHANGED: Simplified actions format - just join with spaces
    actions_str = " ".join(gs.actions_log)

    # CHANGED: Updated final stacks calculation and ensured stacks are tracked
    update_stacks(gs)  # Make sure stacks are current
    final_stacks = gs.stacks if hasattr(gs, 'stacks') else gs.poker_state.stacks

    winnings_parts = []
    for i in range(len(gs.players)):
        start = starting_stack  # CHANGED: Use starting_stack constant
        final = final_stacks[i]
        net = final - start
        sign = "+" if net > 0 else ""
        winnings_parts.append(f"Player {i+1}: {sign}{net}")

    result_str = "Winnings: " + "; ".join(winnings_parts)

    dealer = f"Player {gs.dealer_index + 1}"
    small_blind_player = f"Player {(gs.dealer_index + 1) % len(gs.players) + 1}"
    big_blind_player = f"Player {(gs.dealer_index + 2) % len(gs.players) + 1}"
    main_info = f"Stack {starting_stack}; Dealer: {dealer}; {small_blind_player} Small blind; {big_blind_player} Big blind"

    # CHANGED: Updated HandHistory.create call to match your required format
    hand = HandHistory.create(
        id=gs.id, 
        mainInfo=main_info, 
        dealt=dealt_str, 
        actions=actions_str, 
        result=result_str
    )

    # CHANGED: Added better error handling for database save
    try:
        HandRepository.save(hand)
        print(f"DEBUG: Hand {gs.id} saved to database")  # ADDED: Debug logging
    except Exception as e:
        print(f"DEBUG: Failed to save hand to database: {e}")  # ADDED: Debug logging
        # Don't raise - just log the error

    _CURRENT_GAME = None
    gs.status = "FINISHED"

    return hand