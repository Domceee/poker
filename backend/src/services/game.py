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
                    # bot decides to call or fold depending on amt
                    decision = random.random()
                    if decision < 0.7 or amt <= big_blind * 2:
                        state.check_or_call()
                        gs.actions_log.append(f"Player {current_index + 1} calls {amt} chips")
                    else:
                        state.fold()
                        gs.actions_log.append(f"Player {current_index + 1} folds")
            elif getattr(state, "can_bet", False) and state.can_bet():
                # bot posts a small bet
                bet_amt = min(big_blind * 2, gs.stacks_start[current_index])
                state.complete_bet_or_raise_to(bet_amt)
                gs.actions_log.append(f"Player {current_index + 1} bets {bet_amt} chips")
            elif getattr(state, "can_fold", False) and state.can_fold():
                state.fold()
                gs.actions_log.append(f"Player {current_index + 1} folds")
            else:
                # unknown state: break to avoid infinite loop
                break
        except Exception:
            # safe fallback: fold
            try:
                state.fold()
                gs.actions_log.append(f"Player {current_index + 1} folds")
            except Exception:
                break

        # When round ends, PokerKit will allow burn/deal board — detect and append board token
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
            elif tok == "x" and state.can_check_or_call() and get_check_call_amount(state) == 0:
                state.check_or_call()
                gs.actions_log.append("Player 1 checks")
            elif tok == "c" and state.can_check_or_call() and get_check_call_amount(state) > 0:
                state.check_or_call()
                gs.actions_log.append("Player 1 calls")
            elif tok.startswith("b") and state.can_bet_or_raise_to():
                amt = int(tok[1:])
                state.bet_or_raise_to(state.commited[0] + amt)
                gs.actions_log.append(f"Player 1 bets {amt} chips")
            elif tok.startswith("r") and state.can_bet_or_raise_to():
                amt = int(tok[1:])
                state.bet_or_raise_to(state.commited[0] + amt)
                gs.actions_log.append(f"Player 1 raises to {amt} chips")
            elif tok == "allin" and state.can_bet_or_raise_to():
                player_stack = gs.stacks_start[0]
                state.bet_or_raise_to(state.commited[0] + player_stack)
                gs.actions_log.append("Player 1 goes all-in")
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

    hands_entries = []
    for seat in range(1, len(gs.players) + 1):
        hc = gs.hole_cards.get(seat, "")
        hands_entries.append(f"Player{seat}: {hc.replace(' ', '')}")
    dealt_str = "Hands: " + "; ".join(hands_entries)

    actions_str = " ".join(gs.actions_log)

    # compute final stacks, net per player
    final_stacks = getattr(state, "stacks", None)
    if final_stacks is None:
        try:
            final_stacks = state.stacks
        except Exception:
            final_stacks = gs.stacks_start

    winnings_parts = []
    for i in range(len(gs.players)):
        start = gs.stacks_start[i]
        final = final_stacks[i]
        net = final - start
        sign = "+" if net > 0 else ""
        winnings_parts.append(f"Player {i+1}: {sign}{net}")

    result_str = "Winnings: " + "; ".join(winnings_parts)

    dealer = f"Player {gs.dealer_index + 1}"
    small_blind = f"Player {(gs.dealer_index + 1) % len(gs.players) + 1}"
    big_blind = f"Player {(gs.dealer_index + 2) % len(gs.players) + 1}"
    main_info = f"Stack {starting_stack}; Dealer: {dealer}; {small_blind} Small blind; {big_blind} Big blind"

    hand = HandHistory.create(id=gs.id, mainInfo=main_info, dealt=dealt_str, actions=actions_str, result=result_str)

    # save via repository
    try:
        HandRepository.save(hand)
    except Exception:
        # if DB save fails, still return hand object (but log/raise in real app)
        pass

    _CURRENT_GAME = None
    gs.status = "FINISHED"

    return hand