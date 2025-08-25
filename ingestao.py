Import fitz
Import docx
From bs4 import BeautifulSoup
From sqlalchemy import create_engine, Column, Integer, String, Text
From sqlalchemy.ext.declarative import declarative_base
From sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://eklesia123@localhost:5432/eklesiaia"
Engine = create_engine(DATABASE_URL) 
Session = Session()
Base = declarative_base()

Class TextoBiblico(Base):
__tablename__ =
Id = Column(Integer, primary_key=True)
Titulo = Column(String)
Conteudo = Column(Text)

Base.metadata.create_all(engine)

Def extrair_pdf(caminho):
Doc = fitz.open(caminho)
Texto = "".join([pagina.get_text() for pagina in doc])
Return texto

Def extrair_docx(caminho):
Doc = docx.Document(caminho)
Return "\n".join([p.text for p in doc.paragraphs])

Def extrair_html(caminho):
With open(caminho, "r", encoding="utf-8) as f:
          Soup = BeautifulSoup(f,"html.parser")
Return soup.get_text()

Def salvar_texto(titulo, conteudo):
Texto = TextoBiblico(titulo=titulo, conteudo=conteudo)
Session.add(texto)
Session.commit()
