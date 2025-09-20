"""
Compatibilidade: reexporta as funções modernas localizadas em app.chat.
Este arquivo existia com uma implementação antiga; para evitar duplicidade
e erros de import, apenas reexportamos as funções utilizadas.
"""

from app.chat import (  # noqa: F401
    responder_pergunta_com_versiculo,
    recuperar_docs,
    stream_resposta,
)

__all__ = [
    "responder_pergunta_com_versiculo",
    "recuperar_docs",
    "stream_resposta",
]
