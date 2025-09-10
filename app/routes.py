from fastapi import APIRouter, Request, File, UploadFile, Form, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import (
    authenticate_user,
    create_access_token,
   
    Token,
    register_user,
)
from app.auth import (
    free_or_authenticated,
    get_current_user,
)
from pydantic import BaseModel
from app.chat import responder_pergunta_com_versiculo
from app.sermoes.generator import (
    gerar_sermao,
    gerar_estudo_biblico,
    gerar_devocional,
    gerar_ebook,
)
from app.ingestor import indexar_conteudo_teologico, processar_arquivo
import os

# Configuração dinâmica do modelo Ollama
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma

from app.biblia_api import (
    buscar_versos_por_palavra,
    buscar_verso_por_referencia,
    listar_biblias_idiomas,
    buscar_recursos_extras,
    buscar_conteudo_multimidia,
    buscar_audio_timestamps,
    listar_idiomas,
    listar_paises,
    buscar_versiculo,
    pesquisar_termo,
    listar_biblias,
    listar_livros,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: str
    full_name: str = ""
    password: str


@router.post("/register")
async def register(data: RegisterRequest):
    if not data.username or not data.email or not data.password:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400, detail="Dados obrigatórios ausentes."
        )
    # Verifica se já existe usuário
    from app.ingestor import get_user_by_username

    if get_user_by_username(data.username):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Usuário já existe.")
    user = register_user(
        data.username,
        data.email,
        data.full_name,
        data.password,
    )
    return {
        "status": "sucesso",
        "mensagem": f"Usuário {user.username} criado.",
    }


# --- AUTENTICAÇÃO JWT ---
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from datetime import timedelta

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- ROTAS BÍBLIA AVANÇADAS ---


@router.get("/biblia/busca-palavra")
async def biblia_busca_palavra(
    palavra: str, limite: int = 50, user=Depends(get_current_user)
):
    """
    Busca todos os versos que contenham a palavra em todos os idiomas
    principais.
    """
    return buscar_versos_por_palavra(palavra, limite=limite)


# Busca por referência (livro/capítulo/versículo)
@router.get("/biblia/busca-referencia")
async def biblia_busca_referencia(
    language_code: str,
    book_id: str,
    chapter_id: str,
    verse_number: str = None,
    user=Depends(free_or_authenticated),
):
    """Busca um verso específico por referência."""
    return buscar_verso_por_referencia(
        language_code, book_id, chapter_id, verse_number
    )


# Listar todas as versões disponíveis nos idiomas desejados
@router.get("/biblia/versoes")
async def biblia_versoes(user=Depends(get_current_user)):
    """
    Lista todas as versões disponíveis em português, espanhol, inglês,
    grego e hebraico.
    """
    return listar_biblias_idiomas()


# Listar recursos extras (áudio, vídeo, etc) de um capítulo
@router.get("/biblia/recursos-extras")
async def biblia_recursos_extras(
    bible_id: str,
    book_id: str,
    chapter_id: str,
    user=Depends(free_or_authenticated),
):
    """Busca recursos extras (áudio, vídeo, etc) para um capítulo."""
    return buscar_recursos_extras(bible_id, book_id, chapter_id)


# Listar multimídia de um capítulo
@router.get("/biblia/multimidia")
async def biblia_multimidia(
    fileset_id: str,
    book: str,
    chapter: str,
    user=Depends(free_or_authenticated),
):
    """Busca conteúdo multimídia (áudio, vídeo, texto) de um capítulo."""
    return buscar_conteudo_multimidia(fileset_id, book, chapter)


# Listar timestamps de áudio
@router.get("/biblia/audio-timestamps")
async def biblia_audio_timestamps(
    fileset_id: str,
    book: str,
    chapter: str,
    user=Depends(free_or_authenticated),
):
    """Busca timestamps de áudio para um capítulo."""
    return buscar_audio_timestamps(fileset_id, book, chapter)


# Listar idiomas disponíveis
@router.get("/biblia/idiomas")
async def biblia_idiomas(user=Depends(get_current_user)):
    return listar_idiomas()


# Listar países disponíveis
@router.get("/biblia/paises")
async def biblia_paises(user=Depends(get_current_user)):
    return listar_paises()


@router.post("/perguntar")
async def perguntar(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    pergunta = data.get("pergunta")
    resposta = responder_pergunta_com_versiculo(pergunta)
    return {"resposta": resposta}


@router.post("/gerar-sermao")
async def gerar(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    tipo = data.get("tipo", "expositivo")
    tema = data.get("tema", "graça")
    versiculos = data.get("versiculos", ["Efésios 2:8"])
    num_topicos = data.get("num_topicos", 3)
    autor = data.get("autor")
    resultado = gerar_sermao(tipo, tema, versiculos, num_topicos, autor)
    return resultado


@router.post("/indexar-conteudo")
async def indexar_conteudo(user=Depends(get_current_user)):
    try:
        indexar_conteudo_teologico()
        return {"status": "sucesso", "mensagem": "Conteúdo indexado na IA."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}


@router.get("/versiculo")
async def versiculo(
    language_code: str,
    book_id: str,
    chapter_id: int,
    verse_number: int = None,
    user=Depends(free_or_authenticated),
):
    resultado = buscar_versiculo(
        language_code,
        book_id,
        chapter_id,
        verse_number,
    )
    return resultado


@router.get("/pesquisar-termo")
async def pesquisar(
    termo: str,
    page: int = 1,
    limit: int = 5,
    user=Depends(free_or_authenticated),
):
    resultado = pesquisar_termo(termo, page, limit)
    return resultado


@router.get("/biblias")
async def biblias(user=Depends(get_current_user)):
    return listar_biblias()


@router.get("/livros")
async def livros(bible_id: str, user=Depends(get_current_user)):
    return listar_livros(bible_id)


@router.post("/gerar-estudo")
async def gerar_estudo(
    request: Request,
    user=Depends(get_current_user),
):
    data = await request.json()
    tema = data.get("tema")
    versiculos = data.get("versiculos", [])
    autor = data.get("autor")
    resultado = gerar_estudo_biblico(tema, versiculos, autor)
    return resultado


@router.post("/gerar-devocional")
async def gerar_devocional_endpoint(
    request: Request, user=Depends(get_current_user)
):
    data = await request.json()
    tema = data.get("tema")
    versiculo = data.get("versiculo")
    autor = data.get("autor")
    resultado = gerar_devocional(tema, versiculo, autor)
    return resultado


@router.post("/gerar-ebook")
async def gerar_ebook_endpoint(
    request: Request,
    user=Depends(get_current_user),
):
    data = await request.json()
    tema = data.get("tema")
    capitulos = data.get("capitulos", 5)
    autor = data.get("autor")
    resultado = gerar_ebook(tema, capitulos, autor)
    return resultado


@router.post("/upload-arquivo")
async def upload_arquivo(
    arquivo: UploadFile = File(...),
    tipo: str = Form(...),
    autor: str = Form(None),
    tema: str = Form(None),
    fonte: str = Form(None),
    user=Depends(free_or_authenticated),
):
    caminho_temp = f"temp_{arquivo.filename}"
    with open(caminho_temp, "wb") as f:
        f.write(await arquivo.read())
    try:
        processar_arquivo(caminho_temp, tipo, autor, tema, fonte)
        return {"status": "sucesso", "mensagem": "Arquivo salvo e indexado."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
    finally:
        os.remove(caminho_temp)


def escolher_modelo(tipo_conteudo, pergunta=None, tema=None, versiculos=None):
    texto_base = (pergunta or "") + (tema or "")
    tamanho = len(texto_base)
    if versiculos:
        tamanho += sum(len(v) for v in versiculos)
    if "devocional" in texto_base.lower():
        return "mistral"
    if "sermão" in texto_base.lower() or "estudo" in texto_base.lower():
        return "gemma3"
    if tamanho < 80 or "explicar" in texto_base.lower():
        return "phi3"
    return "gemma3"


@router.post("/pergunta-unificada")
async def pergunta_unificada(
    request: Request, 
    user=Depends(free_or_authenticated)
):
    data = await request.json()
    pergunta = data.get("pergunta")
    tipo_conteudo = data.get("tipo_conteudo", "resposta")
    tema = data.get("tema")
    autor = data.get("autor")
    versiculos = data.get("versiculos", [])
    modelo = escolher_modelo(tipo_conteudo, pergunta, tema, versiculos)
    embedding_model = OllamaEmbeddings(model=modelo)
    db = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embedding_model,
    )
    resposta_acervo = (
        db.similarity_search(pergunta, k=1)[0].page_content
        if db
        else ""
    )
    if tipo_conteudo == "estudo":
        resultado = gerar_estudo_biblico(tema or pergunta, versiculos, autor)
    elif tipo_conteudo == "devocional":
        resultado = gerar_devocional(
            tema or pergunta, versiculos[0] if versiculos else None, autor
        )
    elif tipo_conteudo == "ebook":
        resultado = gerar_ebook(tema or pergunta, 5, autor)
    elif tipo_conteudo == "sermao":
        resultado = gerar_sermao(
            "expositivo", tema or pergunta, versiculos, 3, autor
        )
    else:
        resultado = {"resposta": resposta_acervo}
    resultado["resposta_acervo"] = resposta_acervo
    resultado["modelo_usado"] = modelo
    return resultado
