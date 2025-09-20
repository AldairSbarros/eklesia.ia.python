"""
Compatibilidade: reexporta o router moderno localizado em app.routes.
Este arquivo existia com código inválido; mantemos apenas o router para
evitar confusão.
"""

from app.routes import router  # noqa: F401

__all__ = ["router"]
