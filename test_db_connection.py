import os
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

# Carrega a string de conexão do .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///conteudo_teologico.db")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Conexão bem-sucedida ao banco de dados!")
except OperationalError as e:
    print(f"Erro ao conectar: {e}")
