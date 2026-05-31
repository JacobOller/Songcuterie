import os

from dotenv import load_dotenv

# Load .env before routers import mood_parser (which needs GOOGLE_API_KEY).
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers import auth, search, user

app = FastAPI()

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(user.router)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
