from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama


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


def buscar_versiculo(referencia: str) -> str:
    # Exemplo simples de busca de versículo (substitua por lógica real
    # conforme necessário)
    versiculos = {
        "João 3:16": (
            "Porque Deus amou o mundo de tal maneira que deu o seu Filho "
            "unigênito, para que todo aquele que nele crê não pereça, mas "
            "tenha a vida eterna."
        )
    }
    return versiculos.get(referencia, "")


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
