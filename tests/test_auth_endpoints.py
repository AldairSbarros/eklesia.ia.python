import os
import io
import uuid
from fastapi.testclient import TestClient

# Configura ambiente (tests usam SQLite e RAG simulado)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_app.db")
os.environ.setdefault("EKLESIA_MOCK_RAG", "1")


def test_register_login_and_perguntar_and_upload():
    # Importa app depois de configurar env
    from main import app
    client = TestClient(app)
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "Secr3t!1"

    # 1) Register
    r = client.post(
        "/register",
        json={
            "username": username,
            "email": email,
            "full_name": "Tester",
            "password": password,
        },
    )
    assert r.status_code == 200, r.text

    # 2) Login
    r = client.post(
        "/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json().get("access_token")
    assert token

    # 3) Perguntar (com token)
    r = client.post(
        "/perguntar",
        json={"pergunta": "O que é graça?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "resposta" in data

    # 4) Upload (sem token, usa free_or_authenticated)
    content = io.BytesIO(b"Conteudo de teste simples")
    files = {"arquivo": ("teste.txt", content, "text/plain")}
    r = client.post(
        "/upload-arquivo",
        files=files,
        data={
            "tipo": "txt",
            "autor": "Anon",
            "tema": "Teste",
            "fonte": "UnitTest",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "sucesso"
