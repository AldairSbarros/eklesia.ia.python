
# app/chat.py
from __future__ import annotations

import os
import importlib
import re
from typing import Any, Dict, List, AsyncIterator
from typing import Any as _Any
from types import SimpleNamespace

from dotenv import load_dotenv

# Imports de LangChain/Ollama/Chroma serão resolvidos sob demanda
OllamaLLM = None
OllamaEmbeddings = None
Chroma = None
RetrievalQA = None
ChatPromptTemplate = None
RunnablePassthrough = None
RunnableLambda = None
StrOutputParser = None

# Tenta usar a API real; se não existir, usa fallback local
try:
    from app.biblia_api import buscar_versiculo as _buscar_versiculo_api
except Exception:
    _buscar_versiculo_api = None

# ----------------------------
# Configurações por ambiente
# ----------------------------
load_dotenv()

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "eklesia")

# LLM de geração (Ollama)
LLM_MODEL = (
    os.getenv("OLLAMA_LLM_MODEL")
    or os.getenv("OLLAMA_MODEL")
    or "mistral"
)  # ex.: "mistral", "llama3.1:8b"

# Modelo de embeddings (Ollama)
EMBED_MODEL = os.getenv(
    "OLLAMA_EMBED_MODEL", "bge-m3"
)  # ex.: "bge-m3", "nomic-embed-text"

# Flag para simular RAG (útil em smoke tests/ambientes sem modelos baixados)
MOCK_RAG = os.getenv("EKLESIA_MOCK_RAG", "0").lower() in {"1", "true", "yes"}

# ----------------------------
# Modelos / Vectorstore
# ----------------------------
if not MOCK_RAG:
    try:
        _ollama = importlib.import_module("langchain_ollama")
        _chroma = importlib.import_module("langchain_chroma")
        _chains = importlib.import_module("langchain.chains")
        _prompts = importlib.import_module("langchain.prompts")
        _runnables = importlib.import_module("langchain_core.runnables")
        _parsers = importlib.import_module("langchain_core.output_parsers")

        _OllamaLLM = getattr(_ollama, "OllamaLLM")
        _OllamaEmbeddings = getattr(_ollama, "OllamaEmbeddings")
        _Chroma = getattr(_chroma, "Chroma")
        _RetrievalQA = getattr(_chains, "RetrievalQA")
        _ChatPromptTemplate = getattr(_prompts, "ChatPromptTemplate")
        _RunnablePassthrough = getattr(_runnables, "RunnablePassthrough")
        _RunnableLambda = getattr(_runnables, "RunnableLambda")
        _StrOutputParser = getattr(_parsers, "StrOutputParser")

        # Bind símbolos globais
        OllamaLLM = _OllamaLLM
        OllamaEmbeddings = _OllamaEmbeddings
        Chroma = _Chroma
        RetrievalQA = _RetrievalQA
        ChatPromptTemplate = _ChatPromptTemplate
        RunnablePassthrough = _RunnablePassthrough
        RunnableLambda = _RunnableLambda
        StrOutputParser = _StrOutputParser

        llm = OllamaLLM(model=LLM_MODEL)
        embeddings = OllamaEmbeddings(model=EMBED_MODEL)
        db = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings,
        )
        retriever = db.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 8, "score_threshold": 0.25},
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,
            chain_type="stuff",
        )
    except Exception:
        # Falha em importar/instanciar: entra em modo MOCK
        MOCK_RAG = True
        llm = None
        embeddings = None
        db = None
        retriever = None
        qa_chain = None
else:
    llm = None
    embeddings = None
    db = None
    retriever = None
    qa_chain = None

# ----------------------------
# Auxiliares
# ----------------------------
_SALVACAO_REGEX = re.compile(
    (
        r"\b("
        r"salva(ç|c)ã(o|a|os|ões)|"
        r"redentor(a|es)?|"
        r"reden(ç|c)ão|"
        r"salvar|"
        r"salvo[s]?"
        r")\b"
    ),
    re.IGNORECASE,
)


def _format_sources(docs: List[Any]) -> List[Dict[str, Any]]:
    fontes: List[Dict[str, Any]] = []
    for d in docs or []:
        m = d.metadata or {}
        fontes.append({
            "source": (
                m.get("source")
                or m.get("file_path")
                or "desconhecido"
            ),
            "page": m.get("page"),
            "score": getattr(d, "score", None),  # pode não existir
        })
    return fontes


def buscar_versiculo(referencia: str) -> str:
    """
    Usa a API real, se disponível; senão fallback estático (apenas para dev).
    """
    if _buscar_versiculo_api:
        try:
            return _buscar_versiculo_api(referencia)
        except Exception:
            pass

    # Fallback mínimo
    versiculos = {
        "João 3:16": (
            "Porque Deus amou o mundo de tal maneira que deu o seu "
            "Filho unigênito, para que todo aquele que nele crê não "
            "pereça, mas tenha a vida eterna."
        )
    }
    return versiculos.get(referencia, "")


# ----------------------------
# Função principal
# ----------------------------
def responder_pergunta_com_versiculo(pergunta: str) -> Dict[str, Any]:
    """
    Responde com base no acervo (RAG) + injeta João 3:16 quando a pergunta
    trata de 'salvação'. Retorna também as fontes (quando houver).
    """
    pergunta = (pergunta or "").strip()
    if not pergunta:
        return {
            "resposta": "Por favor, forneça uma pergunta.",
            "fontes": [],
        }

    if MOCK_RAG:
        resposta = f"[MOCK] Resposta simulada para: {pergunta}"
        fontes = [{"source": "mock.txt", "page": 1, "score": 0.99}]
    else:
        # Use invoke com dict para pegar result + source_documents
        result = qa_chain.invoke({"query": pergunta})
        resposta = (result.get("result") or "").strip()
        fontes = _format_sources(result.get("source_documents"))

    # Se não houve fontes relevantes, avisa na resposta
    if not fontes:
        resposta = (
            "Não encontrei trechos suficientemente relevantes no acervo para "
            "responder com confiança. Aqui vai uma resposta geral com base no "
            "modelo:\n\n"
        ) + (resposta or "—")

    # Injeta versículo quando apropriado (sem quebrar se API falhar)
    try:
        if _SALVACAO_REGEX.search(pergunta):
            v = buscar_versiculo("João 3:16")
            if v:
                resposta += f"\n\n📖 **João 3:16** — {v}"
    except Exception:
        # Nunca deixa a falha da API derrubar a resposta principal
        pass

# (imports moved to top of file)
# Duplicate imports removed; already imported at the top.


def _format_docs_text(docs: list) -> str:
    """Concatena conteúdos de documentos para o contexto do prompt."""
    parts = []
    for d in docs or []:
        txt = getattr(d, "page_content", "") or ""
        parts.append(txt.strip())
    return "\n\n---\n\n".join(p for p in parts if p)


def _build_prompt() -> _Any:
    """Prompt para respostas teológicas com fontes."""
    system = (
        "Você é um assistente teológico que responde com base nos trechos "
        "fornecidos no CONTEXTO.\n"
        "Regras:\n"
        "- Seja fiel ao CONTEXTO; se a resposta não estiver no contexto, "
        "diga que não encontrou evidências suficientes.\n"
        "- Cite fontes quando possível (arquivo/página), em Markdown.\n"
        "- Seja claro e biblicamente acurado.\n"
    )
    # Import seguro caso esteja em modo não-MOCK
    _prompts = importlib.import_module("langchain.prompts")
    _ChatPromptTemplate = getattr(_prompts, "ChatPromptTemplate")
    template = _ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Pergunta: {question}\n\nCONTEXTO:\n{context}"),
        ]
    )
    return template


def recuperar_docs(pergunta: str, k: int = 8, score_threshold: float = 0.25):
    """
    Recupera documentos relevantes e formata fontes.
    Usa o retriever já configurado em módulo (db.as_retriever(...)).
    """
    # O retriever já foi criado com threshold no módulo.
    # Se quiser, here override:
    # local_retriever = db.as_retriever(
    #     search_type="similarity_score_threshold",
    #     search_kwargs={"k": k, "score_threshold": score_threshold}
    # )
    # docs = local_retriever.get_relevant_documents(pergunta)
    if MOCK_RAG:
        docs = [SimpleNamespace(page_content=f"[MOCK CONTEXTO] {pergunta}")]
    else:
        docs = retriever.get_relevant_documents(pergunta)

    fontes = []
    for d in docs or []:
        m = d.metadata or {}
        fontes.append(
            {
                "source": (
                    m.get("source")
                    or m.get("file_path")
                    or "desconhecido"
                ),
                "page": m.get("page"),
            }
        )
    return docs, fontes


async def stream_resposta(
    pergunta: str,
    docs: list | None = None
) -> AsyncIterator[str]:
    """
    Faz streaming da resposta do LLM usando LCEL (prompt | llm | parser).
    Se 'docs' não for passado, recupera antes (bloqueio rápido) e
    streama apenas a geração.
    Retorna chunks de texto (tokens) como strings.
    """
    pergunta = (pergunta or "").strip()
    if not pergunta:
        # Em SSE, você pode mandar um evento único com erro e encerrar
        yield "Por favor, forneça uma pergunta."
        return

    # Recupera docs uma vez (fora do stream de tokens)
    if docs is None:
        docs, _ = recuperar_docs(pergunta)

    if MOCK_RAG:
        text = f"[MOCK STREAM] Resposta para: {pergunta}"
        for part in text.split():
            yield part + " "
        return

    context = _format_docs_text(docs)
    prompt = _build_prompt()
    parser = StrOutputParser()

    chain = prompt | llm | parser
    async for chunk in chain.astream({
        "question": pergunta,
        "context": context
    }):
        yield chunk
