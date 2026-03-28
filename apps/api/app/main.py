from fastapi import FastAPI

from app.routers.auth import router as auth_router
from db.base import Base
from db.session import engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
