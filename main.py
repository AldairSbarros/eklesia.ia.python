import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import router
from sqlalchemy import text
from app.ingestor import engine
from fastapi import HTTPException

# Carrega variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="EKLESIA IA",
    description=(
        "API para perguntas teológicas com RAG "
        "(LangChain + Ollama + Chroma)"
    ),
    version="1.0.0",
)

# CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(router)

# Healthcheck


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API EKLESIA IA está rodando"}


@app.get("/db/health", tags=["Health"])
def db_health_check():
    """Verifica conectividade com o banco configurado em DATABASE_URL."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        # Força status 503 para facilitar healthcheck do container
        raise HTTPException(status_code=503, detail=str(e))
