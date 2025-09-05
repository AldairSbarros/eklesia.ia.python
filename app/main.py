from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Eklesia IA")
app.include_router(router)
