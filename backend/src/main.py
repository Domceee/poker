from fastapi import FastAPI
from api.routes import router as api_router
from routers.players import router as players_router

app = FastAPI()

app.include_router(api_router)
app.include_router(players_router)

@app.get("/")
def root():
    return {"message": "Game is running"}