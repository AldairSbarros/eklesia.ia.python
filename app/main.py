
# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import (
    router,
)  # Certifique-se que app/routes.py existe e tem o router

# ----------------------------
# Carregar variáveis de ambiente
# ----------------------------
load_dotenv()

# ----------------------------
# Configuração da API
# ----------------------------
app = FastAPI(
    title="EKLESIA IA",
    description=(
        "API para perguntas teológicas com RAG (LangChain + Ollama + Chroma)"
    ),
    version="1.0.0",
)

# ----------------------------
# CORS (necessário para frontend)
# ----------------------------
origins = os.getenv("CORS_ORIGINS", "*").split(",")
"""Ex.: "http://localhost:3000"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Rotas
# ----------------------------
app.include_router(router)

# ----------------------------
# Healthcheck
# ----------------------------


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API EKLESIA IA está rodando"}
