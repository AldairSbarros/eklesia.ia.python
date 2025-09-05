import pytest
from app.biblia_api import buscar_versiculo, pesquisar_termo, listar_biblias
from app.ingestor import (
    extrair_pdf,
    extrair_docx,
    extrair_html,
    extrair_txt,
    extrair_ppt as extrair_pptx,
    ConteudoTeologico,
    session
)
from sqlalchemy import select
import requests
import os

# Configurações da API da Bíblia
BIBLE_API_URL = os.getenv("BIBLE_API_URL", "https://4.dbt.io/api")
BIBLE_API_KEY = os.getenv("BIBLE_API_KEY", "")

# Função utilitária para buscar códigos válidos na API DBT


def get_valid_bible_and_verse():
    # Buscar bíblias em português
    resp = requests.get(
        f"{BIBLE_API_URL}/bibles?language_code=por&v=4&key={BIBLE_API_KEY}"
    )
    data = resp.json().get("data", []) if resp.status_code == 200 else []
    if not data:
        return None
    bible_id = data[0]["abbr"]
    # Buscar filesets
    resp2 = requests.get(
        f"{BIBLE_API_URL}/bibles/{bible_id}?v=4&key={BIBLE_API_KEY}"
    )
    filesets_obj = (
        resp2.json().get("data", {}).get("filesets", {})
        if resp2.status_code == 200 else {}
    )
    filesets = [
        fs
        for fs_list in filesets_obj.values()
        for fs in fs_list
        if fs.get("type", "").startswith("text")
        or fs.get("set_type_code", "").startswith("text")
    ]
    if not filesets:
        return None
    fileset_id = filesets[0]["id"]
    # Buscar livros
    resp3 = requests.get(
        f"{BIBLE_API_URL}/bibles/{bible_id}/book?v=4&key={BIBLE_API_KEY}"
    )
    livros = resp3.json().get("data", []) if resp3.status_code == 200 else []
    if not livros:
        return None
    # Iterar sobre livros, capítulos e versículos até encontrar um válido
    for livro in livros:
        chapters = livro.get("chapters")
        if chapters and isinstance(chapters, list):
            for chapter_id in chapters:
                # Buscar conteúdo do capítulo
                url = (
                    f"{BIBLE_API_URL}/bibles/filesets/{fileset_id}/"
                    f"{livro['book_id']}/{chapter_id}?v=4&key={BIBLE_API_KEY}"
                )
                resp4 = requests.get(url)
                if resp4.status_code == 200:
                    data = resp4.json().get(
                        "data", []
                    )
                    if data and isinstance(data, list):
                        for verse in data:
                            verse_number = (
                                verse.get("verse_start")
                                or verse.get("verse_sequence")
                                or verse.get("verse")
                            )
                            if verse_number:
                                return (
                                    bible_id,
                                    fileset_id,
                                    livro["book_id"],
                                    chapter_id,
                                    verse_number,
                                )
    return None

# Teste da API da Bíblia


@pytest.mark.parametrize(
    "language_code, book_id, chapter_id, verse_number",
    [
        ("por", "GEN", 1, 1),
        ("por", "JOH", 3, 16)
    ]
)
def test_buscar_versiculo(language_code, book_id, chapter_id, verse_number):
    resultado = buscar_versiculo(
        language_code, book_id, chapter_id, verse_number
    )
    assert resultado is not None
    assert (
        "verse" in resultado
        or "text" in resultado
        or "verse_text" in resultado
    )


def test_pesquisar_termo():
    resultado = pesquisar_termo("graça")
    assert resultado is not None
    assert "data" in resultado


def test_listar_biblias():
    biblias = listar_biblias()
    assert biblias is not None
    assert isinstance(biblias, list)

# Teste de leitura de arquivos PDF, DOCX, HTML, TXT, PPTX


def test_extrair_pdf():
    caminho = "tests/files/teste.pdf"
    texto = extrair_pdf(caminho)
    assert texto and isinstance(texto, str)


def test_extrair_docx():
    caminho = "tests/files/teste.docx"
    texto = extrair_docx(caminho)
    assert texto and isinstance(texto, str)


def test_extrair_html():
    caminho = "tests/files/teste.html"
    texto = extrair_html(caminho)
    assert texto and isinstance(texto, str)


def test_extrair_txt():
    caminho = "tests/files/teste.txt"
    texto = extrair_txt(caminho)
    assert texto and isinstance(texto, str)


def test_extrair_pptx():
    caminho = "tests/files/teste.pptx"
    texto = extrair_pptx(caminho)
    assert texto and isinstance(texto, str)


# Teste de consulta ao banco de dados
def test_db_consulta():
    resultado = session.execute(select(ConteudoTeologico)).scalars().all()
    assert isinstance(resultado, list)

# Teste de integração IA (simples)


def test_integracao_ia():
    from app.chat import responder_pergunta_com_versiculo
    resposta = responder_pergunta_com_versiculo("O que é graça?")
    assert resposta and isinstance(resposta, str)

# Teste dinâmico de busca de versículo com códigos válidos


def test_buscar_versiculo_valido():
    result = get_valid_bible_and_verse()
    assert result is not None, (
        "Não foi possível obter códigos válidos da API DBT."
    )
    bible_id, fileset_id, book_id, chapter_id, verse_number = result
    from app.biblia_api import buscar_versiculo
    versiculo = buscar_versiculo(
        "por", book_id, chapter_id, verse_number, fileset_id=fileset_id
    )
    assert versiculo is not None
    assert (
        "verse" in versiculo
        or "text" in versiculo
        or "verse_text" in versiculo
    )
