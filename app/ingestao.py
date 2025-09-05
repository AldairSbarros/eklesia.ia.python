import fitz
import docx
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://aldai:2025@localhost:5432/eklesia_ia_db"
)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class TextoBiblico(Base):
    __tablename__ = "textos_biblicos"
    id = Column(Integer, primary_key=True)
    titulo = Column(String)
    conteudo = Column(Text)


Base.metadata.create_all(engine)


def extrair_pdf(caminho):
    doc = fitz.open(caminho)
    texto = "".join([pagina.get_text() for pagina in doc])
    return texto


def extrair_docx(caminho):
    doc = docx.Document(caminho)
    return "\n".join([p.text for p in doc.paragraphs])


def extrair_html(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        return soup.get_text()


def salvar_texto(titulo, conteudo):
    texto = TextoBiblico(titulo=titulo, conteudo=conteudo)
    session.add(texto)
    session.commit()
