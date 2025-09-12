from fastapi import FastAPI
from app.routes import routes

app = FastAPI(title="EKLESIA IA")
app.include_router(routes)
