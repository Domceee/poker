from pokerkit import Automation, NoLimitTexasHoldem
import uuid
from src.models.hand import HandHistory
from src.models.player import Player
from src.models.game_state import GameState
from src.repositories.hand_repo import HandRepository
import random
from typing import Optional

_ACTIVE_GAMES: dict[str, GameState] = {}

big_blind = 40
small_blind = 20
starting_stack = 10000

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

def start_hand(num_players: int = 6, dealer_index: int = 0) -> GameState:
    players = [Player.create(i+1) for i in range(num_players)]
    poker_state = create_state(num_players)

    dealer = dealer_index + 1
    sb = (dealer_index + 1) % num_players + 1
    bb = (dealer_index + 2) % num_players + 1

    hole_cards = {}
    for i in range(num_players):
        cards = poker_state.deal_hole()
        hole_cards[i + 1] = str(cards)

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
    _ACTIVE_GAMES[game_id] = gs

    for i, cards in hole_cards.items():
        gs.actions_log.append(f"Player {i} is dealt {cards}")

    gs.actions_log.append(f"{dealer} is the dealer")
    gs.actions_log.append(f"{sb} posts small blind - {small_blind} chips")
    gs.actions_log.append(f"{bb} posts big blind - {big_blind} chips")

    return gs

def get_state(game_id: str) -> Optional[GameState]:
    return _ACTIVE_GAMES.get(game_id)

def append_board_token(gs: GameState):
    state = gs.poker_state
    if hasattr(state, "board_cards") and state.board_cards:
        token = "".join(str(c) for c in state.board_cards)
        # append token as a single action element
        gs.actions_log.append(token)
        gs.board = [str(c) for c in state.board_cards]

def actor_indices(state):
    return getattr(state, "actor_indices", None)

def get_check_call_amount(state) -> int:
    return getattr(state, "checking_or_calling_amount", 0) or 0

def bots_act_until_user_turn(gs: GameState):
    state = gs.poker_state

    # loop while there are actors and next actor is not seat 1 (index 0)
    while actor_indices(state):
        current_index = state.actor_indices[0]  # 0-based index in PokerKit
        # convert to seat number (1..N) if needed, but we compare to 0 (user seat)
        if current_index == 0:
            # user's turn
            break

        # bot's turn: make decision based on available actions
        try:
            if getattr(state, "can_check_or_call", False) and state.can_check_or_call():
                amt = get_check_call_amount(state)
                if amt == 0:
                    state.check_or_call()
                    gs.actions_log.append("x")
                else:
                    # bot decides to call or fold depending on amt
                    decision = random.random()
                    if decision < 0.7 or amt <= big_blind * 2:
                        state.check_or_call()
                        gs.actions_log.append("c")
                    else:
                        state.fold()
                        gs.actions_log.append("f")
            elif getattr(state, "can_bet", False) and state.can_bet():
                # bot posts a small bet
                bet_amt = min(big_blind * 2, gs.stacks_start[current_index])
                state.complete_bet_or_raise_to(bet_amt)
                gs.actions_log.append(f"b{bet_amt}")
            elif getattr(state, "can_fold", False) and state.can_fold():
                state.fold()
                gs.actions_log.append("f")
            else:
                # unknown state: break to avoid infinite loop
                break
        except Exception:
            # safe fallback: fold
            try:
                state.fold()
                gs.actions_log.append("f")
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

def apply_action(game_id: str, action_token: str) -> GameState:
    """
    Apply a single user action, then progress bots until user's turn again or the hand finishes.
    action_token examples: 'f', 'x', 'c', 'b40', 'r200', 'allin'
    """
    gs = get_state(game_id)
    if gs is None:
        raise KeyError("Game not found")

    state = gs.poker_state

    # if no actor indices, progress board cards first (if applicable)
    if not actor_indices(state):
        if getattr(state, "can_burn_card", False) and state.can_burn_card():
            state.burn_card()
        if getattr(state, "can_deal_board", False) and state.can_deal_board():
            state.deal_board()
            append_board_token(gs)

    # ensure it's user's turn; if not, let bots act until it is
    if actor_indices(state) and state.actor_indices[0] != 0:
        bots_act_until_user_turn(gs)
        # after bots, check again
        if not actor_indices(state):
            if getattr(state, "can_deal_board", False) and state.can_deal_board():
                state.deal_board()
                append_board_token(gs)

    # Now apply user action if actor is user
    if actor_indices(state) and state.actor_indices[0] == 0:
        tok = action_token.strip().lower()
        try:
            if tok == "f":
                state.fold()
                gs.actions_log.append("f")
            elif tok == "x":
                state.check_or_call()
                gs.actions_log.append("x")
            elif tok == "c":
                state.check_or_call()
                gs.actions_log.append("c")
            elif tok.startswith("b"):
                amt = int(tok[1:])
                state.complete_bet_or_raise_to(amt)
                gs.actions_log.append(f"b{amt}")
            elif tok.startswith("r"):
                amt = int(tok[1:])
                state.complete_bet_or_raise_to(amt)
                gs.actions_log.append(f"r{amt}")
            elif tok == "allin":
                # try all-in (raise to player's stack)
                # pokerkit may have method for allin; approximate by using big amount
                player_stack = gs.stacks_start[0]
                state.complete_bet_or_raise_to(player_stack)
                gs.actions_log.append("allin")
            else:
                # fallback: check or call
                state.check_or_call()
                token = "x" if get_check_call_amount(state) == 0 else "c"
                gs.actions_log.append(token)
        except Exception:
            # if invalid action for pokerkit, default to fold as safe
            try:
                state.fold()
                gs.actions_log.append("f")
            except Exception:
                pass

    # after user acted, let bots continue until it's user's turn again or hand finishes
    bots_act_until_user_turn(gs)

    # finally handle board dealing if needed
    if not actor_indices(state):
        if getattr(state, "can_burn_card", False) and state.can_burn_card():
            state.burn_card()
        if getattr(state, "can_deal_board", False) and state.can_deal_board():
            state.deal_board()
            append_board_token(gs)

    # if hand finished, finalize and persist
    finished_flag = False
    # pokerkit might expose status via .status.name or .status
    status_value = getattr(state, "status", None)
    if status_value is not None:
        if getattr(status_value, "name", None) == "FINISHED" or status_value == "FINISHED":
            finished_flag = True

    if finished_flag:
        finalize_hand(gs)

    return gs

def finalize_hand(gs: GameState) -> HandHistory:
    state = gs.poker_state

    # build dealt string
    hands_entries = []
    for seat in range(1, len(gs.players) + 1):
        hc = gs.hole_cards.get(seat, "")
        hands_entries.append(f"Player{seat}: {hc.replace(' ', '')}")
    dealt_str = "Hands: " + "; ".join(hands_entries)

    # actions string: join tokens with spaces; spec shows spaces between board tokens and actions
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

    # main info: dealer + blinds
    dealer = f"Player {gs.dealer_index + 1}"
    small_blind = f"Player {(gs.dealer_index + 1) % len(gs.players) + 1}"
    big_blind = f"Player {(gs.dealer_index + 2) % len(gs.players) + 1}"
    main_info = f"Stack {starting_stack}; Dealer: {dealer}; {small_blind} Small blind; {big_blind} Big blind"

    # Hand id: use gs.id
    hand = HandHistory.create(id=gs.id, mainInfo=main_info, dealt=dealt_str, actions=actions_str, result=result_str)

    # save via repository
    try:
        HandRepository.save(hand)
    except Exception:
        # if DB save fails, still return hand object (but log/raise in real app)
        pass

    # remove in-memory game
    _ACTIVE_GAMES.pop(gs.id, None)
    gs.status = "FINISHED"

    return hand