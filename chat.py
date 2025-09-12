from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from app.biblia_api import buscar_versiculo

llm = OllamaLLM(model="gemma:2b")
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
    resposta = qa_chain.run(pergunta)
    if "salvação" in pergunta.lower():
        versiculo = buscar_versiculo("João 3:16")
        resposta += f"\nJoão 3:16 - {versiculo}"
    return resposta