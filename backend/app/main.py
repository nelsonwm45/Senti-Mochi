from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers import auth, users, google_auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Finance AI Platform")

origins = [
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(google_auth.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Finance AI Platform API"}
