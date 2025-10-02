from fastapi import FastAPI
from app.routes import auth, user

app = FastAPI(title="Scalable FastAPI App")

app.include_router(auth.router)
app.include_router(user.router)
