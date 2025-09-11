from fastapi import FastAPI, HTTPException
from src.repositories.hand_repo import HandRepository
from routers.players import router as players_router
from src.services.game import play_hand
from src.models.hand import HandHistory

app = FastAPI()
repo = HandRepository()

#app.include_router(api_router)
#app.include_router(players_router)

@app.get("/")
def root():
    return {"message": "Game is running"}

@app.post("/hands/", response_model=HandHistory)
def create_hand(user_actions: list[str]):
    hand = play_hand(user_actions)
    repo.add_hand(hand)
    return hand

@app.get("/hands/{hand_id}", response_model=HandHistory)
def get_hand(hand_id: str):
    hand = repo.get_hand(hand_id)
    if not hand:
        raise HTTPException(status_code=404, detail="Hand not found")
    return hand

@app.get("/hands/", response_model=list[HandHistory])
def list_hands():
    return repo.list_hands()