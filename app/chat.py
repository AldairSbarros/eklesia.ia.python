from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
from app.biblia_api import buscar_versiculo

llm = Ollama(model="gemma:2b")
embedding_model = OllamaEmbeddings(model="gemma:2b")
db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_model
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=db.as_retriever(),
    return_source_documents=True
)


def responder_pergunta_com_versiculo(pergunta: str) -> str:
    resultado = qa_chain.invoke(pergunta)
    resposta = resultado.get('result', '')
    if "salvação" in pergunta.lower():
        try:
            versiculo = buscar_versiculo("João 3:16")
            if versiculo:
                resposta += f"\n📖 João 3:16 — {versiculo}"
            else:
                resposta += "\n📖 João 3:16 — Versículo não encontrado."
        except Exception as e:
            resposta += f"\nErro ao buscar versículo: {e}"
    return resposta
