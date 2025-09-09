from fastapi import APIRouter
from models.player import Player

router = APIRouter()

@router.get("/players", response_model=list[Player])

def get_players():
    return [
        Player(id=1, stack=10000),
        Player(id=2, stack=10000),
        Player(id=3, stack=10000),
        Player(id=4, stack=10000),
        Player(id=5, stack=10000),
        Player(id=6, stack=10000),
    ]