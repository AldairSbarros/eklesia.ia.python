import uvicorn

print("""
==============================
API EKLESIA IA RODANDO NA PORTA 8000
ACESSE: http://127.0.0.1:8000
==============================
""")

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)