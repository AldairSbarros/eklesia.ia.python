from __future__ import annotations


import uuid
from fastapi import status, Form
# from pydantic import BaseModel, Field  # Removido: já importado acima
# Imports opcionais do LangChain/Chroma são feitos dentro das funções

# app/routes.py

import os
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json
from fastapi.responses import StreamingResponse

# Importa configurações de RAG definidas no chat
# Configs específicas serão importadas localmente quando necessário

# --- Módulos internos ---
from app.auth import (
    authenticate_user,
    create_access_token,
    Token,
    register_user,
    free_or_authenticated,
    get_current_user,
)
from app.chat import responder_pergunta_com_versiculo, recuperar_docs
from app.sermoes.generator import (
    gerar_sermao,
    gerar_estudo_biblico,
    gerar_devocional,
    gerar_ebook,  # você importou, mas não havia endpoint;
    # mantive import, se quiser expor avise
)
from app.ingestor import indexar_conteudo_teologico, processar_arquivo
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

# Carrega .env (para UPLOAD_DIR e afins)
load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


# ----------------------------
# Modelos (Pydantic)
# ----------------------------
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: str
    full_name: str = ""
    password: str = Field(..., min_length=6)


class PerguntaRequest(BaseModel):
    pergunta: str = Field(..., min_length=3, description="Pergunta do usuário")


class GerarSermaoRequest(BaseModel):
    tipo: str = Field(default="expositivo")
    tema: str = Field(default="graça")
    versiculos: list[str] = Field(default_factory=lambda: ["Efésios 2:8"])
    num_topicos: int = Field(default=3, ge=1, le=12)
    autor: Optional[str] = None


class GerarEstudoRequest(BaseModel):
    tema: str
    versiculos: list[str] = Field(default_factory=list)
    autor: Optional[str] = None


class GerarDevocionalRequest(BaseModel):
    tema: str
    versiculo: str
    autor: Optional[str] = None


class GerarEbookRequest(BaseModel):
    tema: str
    capitulos: int = Field(default=5, ge=1, le=50)
    autor: Optional[str] = None


class PerguntaUnificadaRequest(BaseModel):
    pergunta: str = Field(..., min_length=3)
    tipo_conteudo: str = Field(
        ..., description="estudo|devocional|ebook|sermao|resposta"
    )
    tema: Optional[str] = None
    autor: Optional[str] = None
    versiculos: list[str] = Field(default_factory=list)


# ----------------------------
# Registro e Autenticação
# ----------------------------
@router.post("/register", tags=["Auth"])
async def register(data: RegisterRequest):
    """
    Cria um novo usuário.
    """
    # Evitar duplicidade de usuário (mantive sua lógica original)
    try:
        from app.ingestor import (
            get_user_by_username
        )  # pode ser um repo seu; se for do auth, mova para app.auth
        if get_user_by_username(data.username):
            raise HTTPException(status_code=400, detail="Usuário já existe.")
    except ImportError:
        # Se não houver esse método, ignore a verificação externa
        pass

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


@router.post("/login", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Realiza login via OAuth2PasswordRequestForm.
    Envie `username` e `password` como `application/x-www-form-urlencoded`.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
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


# ----------------------------
# RAG / Perguntas
# ----------------------------
@router.post("/perguntar", tags=["RAG"])
async def perguntar(
    body: PerguntaRequest,
    user=Depends(free_or_authenticated),
):
    """
    Responde a uma pergunta usando RAG.
    Retorna `resposta` e, se disponível, `fontes`.
    """
    pergunta = body.pergunta.strip()
    if not pergunta:
        raise HTTPException(
            status_code=400,
            detail="Campo 'pergunta' é obrigatório."
        )

    result = responder_pergunta_com_versiculo(pergunta)

    # Compatível com sua função antiga (string) e a versão revisada (dict)
    if isinstance(result, dict):
        # Esperado: {"resposta": str, "fontes": [...]}
        return result

    return {"resposta": str(result), "fontes": []}


# ----------------------------
# Sermões / Estudos / Devocionais
# ----------------------------
@router.post("/gerar-sermao", tags=["Conteúdo"])
async def gerar_sermao_endpoint(
    body: GerarSermaoRequest, user=Depends(get_current_user)
):
    """
    Gera um sermão com base no tipo/tema/versículos.
    """
    resultado = gerar_sermao(
        body.tipo, body.tema, body.versiculos, body.num_topicos, body.autor
    )
    return resultado


@router.post("/gerar-estudo", tags=["Conteúdo"])
async def gerar_estudo_endpoint(
    body: GerarEstudoRequest, user=Depends(get_current_user)
):
    """
    Gera um estudo bíblico.
    """
    resultado = gerar_estudo_biblico(body.tema, body.versiculos, body.autor)
    return resultado


@router.post("/gerar-devocional", tags=["Conteúdo"])
async def gerar_devocional_endpoint(
    body: GerarDevocionalRequest, user=Depends(get_current_user)
):
    """
    Gera um devocional a partir de um tema e um versículo.
    """
    resultado = gerar_devocional(body.tema, body.versiculo, body.autor)
    return resultado


# ----------------------------
# Ingestão / Indexação
# ----------------------------
@router.post("/ingestao/upload", tags=["Ingestão"])
async def ingestao_upload(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """
    Faz upload de um arquivo e o processa (ingestão no Postgres / Chroma se seu
    processar_arquivo fizer isso).
    """
    # Checa extensão básica
    allowed_exts = {".pdf", ".docx", ".html", ".htm", ".txt", ".md"}
    _, ext = os.path.splitext(file.filename or "")
    ext = ext.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Extensão não suportada: {ext}. Suportadas: "
                f"{', '.join(sorted(allowed_exts))}"
            ),
        )

    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        contents = await file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)
    finally:
        await file.close()

    try:
        inserted_id = processar_arquivo(dest_path)
        if not inserted_id:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Falha ao processar o arquivo "
                    "(conteúdo vazio ou erro de extração)."
                ),
            )
        return {
            "status": "sucesso",
            "mensagem": "Arquivo processado com sucesso.",
            "id": inserted_id,
            "path": dest_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indexar-conteudo", tags=["Ingestão"])
async def indexar_conteudo(user=Depends(get_current_user)):
    """
    Dispara a indexação de conteúdo teológico (pipeline batch).
    """
    try:
        indexar_conteudo_teologico()
        return {"status": "sucesso", "mensagem": "Conteúdo indexado na IA."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------
# Bíblia — Consultas e Metadados
# ----------------------------
@router.get("/biblia/busca-palavra", tags=["Bíblia"])
async def biblia_busca_palavra(
    palavra: str, limite: int = 50, user=Depends(get_current_user)
):
    """Busca todos os versos que contenham a palavra nos idiomas principais."""
    return buscar_versos_por_palavra(palavra, limite=limite)


@router.get("/biblia/busca-referencia", tags=["Bíblia"])
async def biblia_busca_referencia(
    language_code: str,
    book_id: str,
    chapter_id: str,
    verse_number: str | None = None,
    user=Depends(free_or_authenticated),
):
    """Busca um verso específico por referência."""
    return buscar_verso_por_referencia(
        language_code, book_id, chapter_id, verse_number
    )


@router.get("/biblia/versoes", tags=["Bíblia"])
async def biblia_versoes(user=Depends(get_current_user)):
    """Lista versões disponíveis (pt, es, en, grego, hebraico)."""
    return listar_biblias_idiomas()


@router.get("/biblia/recursos-extras", tags=["Bíblia"])
async def biblia_recursos_extras(
    bible_id: str,
    book_id: str,
    chapter_id: str,
    user=Depends(free_or_authenticated),
):
    """Busca recursos extras (áudio, vídeo, etc) para um capítulo."""
    return buscar_recursos_extras(bible_id, book_id, chapter_id)


@router.get("/biblia/multimidia", tags=["Bíblia"])
async def biblia_multimidia(
    fileset_id: str,
    book: str,
    chapter: str,
    user=Depends(free_or_authenticated),
):
    """Busca conteúdo multimídia (áudio, vídeo, texto) de um capítulo."""
    return buscar_conteudo_multimidia(fileset_id, book, chapter)


@router.get("/biblia/audio-timestamps", tags=["Bíblia"])
async def biblia_audio_timestamps(
    fileset_id: str,
    book: str,
    chapter: str,
    user=Depends(free_or_authenticated),
):
    """Busca timestamps de áudio para um capítulo."""
    return buscar_audio_timestamps(fileset_id, book, chapter)


@router.get("/biblia/idiomas", tags=["Bíblia"])
async def biblia_idiomas(user=Depends(get_current_user)):
    return listar_idiomas()


@router.get("/biblia/paises", tags=["Bíblia"])
async def biblia_paises(user=Depends(get_current_user)):
    return listar_paises()


@router.get("/versiculo", tags=["Bíblia"])
async def versiculo(
    language_code: str,
    book_id: str,
    chapter_id: int,
    verse_number: int | None = None,
    user=Depends(free_or_authenticated),
):
    """Retorna um versículo específico (parâmetros explícitos)."""
    return buscar_versiculo(
        language_code,
        book_id,
        chapter_id,
        verse_number,
    )


@router.get("/pesquisar-termo", tags=["Bíblia"])
async def pesquisar(
    termo: str,
    page: int = 1,
    limit: int = 5,
    user=Depends(free_or_authenticated),
):
    """Pesquisa por termo; suporta paginação."""
    return pesquisar_termo(termo, page, limit)


@router.get("/biblias", tags=["Bíblia"])
async def biblias(user=Depends(get_current_user)):
    return listar_biblias()


@router.get("/livros", tags=["Bíblia"])
async def livros(bible_id: str, user=Depends(get_current_user)):
    return listar_livros(bible_id)


# ----------------------------
# Gerar eBook
# ----------------------------
@router.post("/gerar-ebook", tags=["Conteúdo"])
async def gerar_ebook_endpoint(
    body: GerarEbookRequest,
    user=Depends(get_current_user),
):
    """
    Gera um eBook a partir de um tema e (opcional) autor/qtde capítulos.
    """
    resultado = gerar_ebook(body.tema, body.capitulos, body.autor)
    return resultado


# ----------------------------
# Upload + Ingestão
# ----------------------------
@router.post("/upload-arquivo", tags=["Ingestão"])
async def upload_arquivo(
    arquivo: UploadFile = File(...),
    tipo: str = Form(...),
    # mantidos para compat; ignorados por enquanto
    autor: str | None = Form(None),
    tema: str | None = Form(None),
    fonte: str | None = Form(None),
    user=Depends(free_or_authenticated),
):
    """
    Faz upload para um arquivo temporário e processa com `processar_arquivo`
    e remove o arquivo em seguida.

    Observação: metadados (tipo, autor, tema, fonte) são ignorados na versão
    atual do `processar_arquivo(path)`. Se quiser persistir esses metadados,
    posso estender o schema do banco e a função de ingestão.
    """
    allowed_exts = {".pdf", ".docx", ".html", ".htm", ".txt", ".md"}
    _, ext = os.path.splitext(arquivo.filename or "")
    ext = ext.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Extensão não suportada: "
                f"{ext}. Suportadas: {', '.join(sorted(allowed_exts))}"
            ),
        )

    uid = uuid.uuid4().hex
    temp_name = f"{uid}_{arquivo.filename}"
    temp_path = os.path.join(UPLOAD_DIR, temp_name)

    try:
        contents = await arquivo.read()
        with open(temp_path, "wb") as f:
            f.write(contents)
    finally:
        await arquivo.close()

    try:
        # Compatível com ingestao.py robusto
        inserted_id = processar_arquivo(temp_path)
        if not inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Falha ao processar o arquivo "
                    "(conteúdo vazio ou erro de extração)."
                ),
            )
        return {
            "status": "sucesso",
            "mensagem": "Arquivo salvo e indexado.",
            "id": inserted_id,
            "path": temp_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Remove o arquivo temporário
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            # Não deixa falha na remoção bloquear a resposta
            pass


# ----------------------------
# Seleção de modelo (LLM)
# ----------------------------
def escolher_modelo(
    tipo_conteudo: str,
    pergunta: str | None = None,
    tema: str | None = None,
    versiculos: list[str] | None = None,
) -> str:
    """
    Heurística simples para escolher LLM de geração (NÃO os embeddings).
    Ajuste os nomes conforme os modelos que você de fato baixou no Ollama.
    """
    base = f"{pergunta or ''} {tema or ''}".lower()
    tamanho = len(base) + sum(len(v) for v in (versiculos or []))

    # Valor padrão para fallback
    DEFAULT_LLM = os.getenv("OLLAMA_LLM_MODEL", "mistral")

    # Exemplos de mapeamento; ajuste para os modelos existentes no seu Ollama:
    if "devocional" in base:
        # ex.: "mistral"
        return os.getenv("OLLAMA_LLM_DEVOCIONAL", DEFAULT_LLM)
    if "sermão" in base or "sermao" in base or "estudo" in base:
        return os.getenv(
            "OLLAMA_LLM_ESTUDO", "mistral"
        )  # ex.: "mistral" ou "llama3.1:8b"
    if tamanho < 80 or "explicar" in base:
        # ex.: "phi3" se você tiver, senão "mistral"
        return os.getenv("OLLAMA_LLM_CURTO", "mistral")
    return DEFAULT_LLM


# ----------------------------
# Pergunta Unificada
# ----------------------------
@router.post("/pergunta-unificada", tags=["RAG"])
async def pergunta_unificada(
    body: PerguntaUnificadaRequest,
    user=Depends(free_or_authenticated),
):
    """
    Endpoint unificado: produz resposta ou gera conteúdo
    (estudo/devocional/ebook/sermão) e agrega um excerto do acervo
    (via Chroma) como contexto/apoio.
    """
    pergunta = body.pergunta.strip()
    tipo_conteudo = body.tipo_conteudo.lower()
    tema = (body.tema or pergunta).strip()
    autor = body.autor
    versiculos = body.versiculos or []

    # 1) Busca no acervo via util do chat (lida com MOCK_RAG internamente)
    try:
        docs, fontes = recuperar_docs(pergunta)
        resposta_acervo = (
            (docs[0].page_content.strip()) if docs else ""
        )
    except Exception:
        resposta_acervo, fontes = "", []
    
    # 2) Escolhe LLM de geração (se necessário)
    modelo = escolher_modelo(tipo_conteudo, pergunta, tema, versiculos)

    # 3) Roteamento por tipo_conteudo
    if tipo_conteudo == "estudo":
        resultado = gerar_estudo_biblico(tema, versiculos, autor)
    elif tipo_conteudo == "devocional":
        resultado = gerar_devocional(
            tema,
            versiculos[0] if versiculos else None,
            autor,
        )
    elif tipo_conteudo == "ebook":
        resultado = gerar_ebook(tema, 5, autor)
    elif tipo_conteudo in {"sermão", "sermao"}:
        resultado = gerar_sermao("expositivo", tema, versiculos, 3, autor)
    else:
        # "resposta" padrão: delega ao seu chat (que pode usar RAG completo)
        result = responder_pergunta_com_versiculo(pergunta)
        if isinstance(result, dict):
            resultado = result
        else:
            resultado = {"resposta": str(result), "fontes": []}

    # 4) Agrega contexto do acervo (não sobrescreve se já houver)
    if isinstance(resultado, dict):
        resultado.setdefault("resposta_acervo", resposta_acervo)
        if "fontes" in resultado and isinstance(resultado["fontes"], list):
            # agrega sem duplicar
            resultado["fontes"].extend(
                f for f in fontes if f not in resultado["fontes"]
            )
        else:
            resultado["fontes"] = fontes
        resultado["modelo_usado"] = modelo
    else:
        # Se sua função de geração retornar string
        resultado = {
            "resposta": str(resultado),
            "resposta_acervo": resposta_acervo,
            "fontes": fontes,
            "modelo_usado": modelo,
        }

    return resultado


@router.post("/perguntar/stream", tags=["RAG"])
async def perguntar_stream(
    body: PerguntaRequest,
    user=Depends(get_current_user),
):
    """
    Streaming da resposta via SSE (Server-Sent Events).
    Eventos enviados:
      - {type: "meta", fontes: [...], modelos: {...}}
      - {type: "token", content: "<texto parcial>"}
      - {type: "versiculo", ref: "João 3:16", texto: "<texto>" } (opcional)
      - {type: "done"}
    """
    pergunta = body.pergunta.strip()
    if not pergunta:
        raise HTTPException(
            status_code=400,
            detail="Campo 'pergunta' é obrigatório.",
        )

    # Recupera docs + fontes uma única vez (antes do streaming)
    from app.chat import (
        recuperar_docs,
        stream_resposta,
        buscar_versiculo,
        _SALVACAO_REGEX,
        LLM_MODEL,
        EMBED_MODEL,
        PERSIST_DIR,
        COLLECTION_NAME,
    )

    docs, fontes = recuperar_docs(pergunta)

    async def event_generator():
        # 1) Evento inicial com metadados e fontes
        meta = {
            "type": "meta",
            "fontes": fontes,
            "modelos": {"llm": LLM_MODEL, "embeddings": EMBED_MODEL},
            "chroma": {
                "persist_dir": PERSIST_DIR,
                "collection": COLLECTION_NAME,
            },
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

        # 2) Stream de tokens
        async for token in stream_resposta(pergunta, docs=docs):
            if not token:
                continue
            data = {"type": "token", "content": token}
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        # 3) Injeta João 3:16 quando apropriado
        try:
            if _SALVACAO_REGEX.search(pergunta):
                v = buscar_versiculo("João 3:16")
                if v:
                    data = {
                        "type": "versiculo",
                        "ref": "João 3:16",
                        "texto": v,
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        except Exception:
            # falha silenciosa: não interrompe o stream
            pass

        # 4) Fim
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
