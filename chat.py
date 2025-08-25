From langchain.embeddings import OllamaEmbeddings
From langchain.vectorstores import Chroma
From langchain.chains import RetrievalQa
From langchain.llms import Ollama
From app.biblia_api import buscar_versiculo

Llm = Ollama(model="gemma:2b")
Embedding_model = OllamaEmbeddings(model="gemma:2b")
Db = Chroma(persist_directory="./chroma_db",embedding_function=embedding_model)

Qa_chain = RetrivalQA.from_chaim_type(Llm=llm,
                                      Retriever=db.as_retriever(),
                                      Return_source_documents=True
                                     )
Def
responder_pergunta_com_versiculo(pergunta: str) -> str:
Resposta = qa_chain.run(pergunta)
if"salvação" in pergunta.lower();
Versiculo = buscar_versiculo("João 3:16")
Resposta +=f"\n João 3:16 - {Versiculo}"
Return resposta
