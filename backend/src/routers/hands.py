from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.game import start_hand, get_state, apply_action
from src.repositories.hand_repo import HandRepository
from fastapi.responses import JSONResponse

router = APIRouter()


class StartRequest(BaseModel):
    num_players: int = 6
    dealer_index: int = 0


class ActionRequest(BaseModel):
    action: str  # 'f', 'x', 'c', 'b40', 'r160', 'allin'


@router.post("/hands/start")
def start(req: StartRequest):
    gs = start_hand(num_players=req.num_players, dealer_index=req.dealer_index)
    return { "game_id": gs.id, "log": gs.actions_log }


@router.get("/hands/{hand_id}")
def api_get_state(hand_id: str):
    gs = get_state(hand_id)
    if not gs:
        # maybe finished and persisted; attempt to get from repository
        saved = HandRepository.get(hand_id)
        if saved:
            return {"finished": True, **saved.__dict__}
        raise HTTPException(status_code=404, detail="Hand not found")

    return {
        "id": gs.id,
        "hole_cards": {1: gs.hole_cards.get(1, "")},
        "actions": gs.actions_log,
        "board": gs.board,
        "stacks": gs.stacks_start,
        "status": gs.status,
    }


@router.post("/hands/{hand_id}/action")
def api_action(hand_id: str, req: ActionRequest):
    try:
        gs = apply_action(hand_id, req.action)
    except KeyError:
        raise HTTPException(status_code=404, detail="Hand not found")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

    if gs.status == "FINISHED":
        # fetch saved history
        saved = HandRepository.get(gs.id)
        return {"finished": True, "hand": saved.__dict__ if saved else None}

    return {
        "id": gs.id,
        "hole_cards": {1: gs.hole_cards.get(1, "")},
        "actions": gs.actions_log,
        "board": gs.board,
        "stacks": gs.stacks_start,
        "status": gs.status,
    }


@router.get("/hands/{hand_id}/result")
def api_result(hand_id: str):
    saved = HandRepository.get(hand_id)
    if not saved:
        raise HTTPException(status_code=404, detail="Result not found")
    return saved.__dict__


# @router.get("/hands/")
# def api_list():
#     hands = HandRepository.list_all()
#     return [h.__dict__ for h in hands]