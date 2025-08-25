From fastapi import APIRouter, Request
From app.chat import
responder_pergunta_com_versiculo
From app.sermoes.generator import gerar_sermao

Router = APIRouter()
@router.post("/perguntar")
Async def perguntar(request: Request):
  Data = await request.json()
  Pergunta = data.get("pergunta")
  Resposta = responder_pergunta_com_versiculo(pergunta)
  Return{"resposta": resposta}

@router.post("/gerar-sermao")
Async def gerar(request: Request):
  Data = await.get("tipo", "expositivo")
  Tema = data.get("tema", "graça")
  Versiculos = data.get("versiculos",['Efesios 2:8"])
  Num_topicos = data.get('num_topicos",3)
  Autor = data.get("autor")
  Resultado = gerar_sermao(tipo, tema, versiculos, num_topicos, autor)
  Return resultado
