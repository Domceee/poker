from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.game import start_hand, get_state, apply_action, _CURRENT_GAME
from src.repositories.hand_repo import HandRepository
from fastapi.responses import JSONResponse

router = APIRouter()


class StartRequest(BaseModel):
    num_players: int = 6
    dealer_index: int = 0


class ActionRequest(BaseModel):
    action: str
    amount: int | None = None


@router.post("/hands/start")
def start(req: StartRequest):
    gs = start_hand(num_players=req.num_players, dealer_index=req.dealer_index)
    return { "game_id": gs.id, "log": gs.actions_log }


@router.post("/hands/action")
def api_action(req: ActionRequest):
    try:
        gs = get_state()
        if not gs:
            raise HTTPException(status_code=404, detail="Hand not found")
        gs = apply_action(gs, req.action, req.amount)
    except KeyError:
        raise HTTPException(status_code=404, detail="Hand not found")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

    if gs.status == "FINISHED":
        saved = HandRepository.get(gs.id)
        return {
            "finished": True, 
            "hand": saved.__dict__ if saved else None,
            "actions": gs.actions_log,
            "id": gs.id,
            "hole_cards": {1: gs.hole_cards.get(1, "")},
            "board": gs.board,
            "stacks": getattr(gs, 'stacks', gs.stacks),
            "status": gs.status,
        }

    return {
        "id": gs.id,
        "hole_cards": {1: gs.hole_cards.get(1, "")},
        "actions": gs.actions_log,
        "board": gs.board,
        "stacks": gs.stacks,
        "status": gs.status,
    }

@router.get("/hands/")
def api_list():
    hands = HandRepository.list_all()
    formatted_hands = []
    
    for hand in hands:
        formatted_hand = f"Hand #{hand.id}\n"
        formatted_hand += f"{hand.mainInfo}\n"
        formatted_hand += f"{hand.dealt}\n"
        formatted_hand += f"Actions: {hand.actions}\n"
        formatted_hand += f"{hand.result}"
        formatted_hands.append(formatted_hand)
    
    return {"hands": formatted_hands}