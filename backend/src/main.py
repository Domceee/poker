from fastapi import FastAPI, HTTPException
from src.db import init_db
from src.routers.hands import router as hands_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "Game running"}

@app.get("/health")
def health():
    return {"status": "ok", "message": "Service is healthy"}

app.include_router(hands_router)