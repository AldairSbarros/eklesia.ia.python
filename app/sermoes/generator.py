from app.chat import responder_pergunta_com_versiculo
from app.biblia_api import buscar_versiculo
from app.sermoes.templates import montar_esboco
from app.sermoes.utils import buscar_autores


def gerar_sermao(tipo, tema, versiculos, num_topicos, autor=None):
    referencias = [buscar_versiculo(v) for v in versiculos]
    base_biblica = "\n".join([
        f"{v} — {texto}"
        for v, texto in zip(versiculos, referencias)
    ])
    citacoes = buscar_autores(tema, autor)
    prompt = (
        f"Crie um sermão {tipo} sobre '{tema}' com {num_topicos} tópicos. "
        f"Use os versículos: {base_biblica}. "
        f"Inclua citações de {autor or 'teólogos relevantes'}."
    )
    resposta = responder_pergunta_com_versiculo(prompt)
    esboco = montar_esboco(resposta, tipo, num_topicos)
    return {
        "tema": tema,
        "tipo": tipo,
        "versiculos": versiculos,
        "autor": autor,
        "esboco": esboco,
        "citacoes": citacoes,
        "texto_gerado": resposta
    }


def gerar_estudo_biblico(tema, versiculos, autor=None):
    prompt = (
        f"Crie um estudo bíblico sobre '{tema}'. "
        f"Use os versículos: {', '.join(versiculos)}. "
        f"Inclua citações de {autor or 'teólogos relevantes'}. "
        "Estruture em introdução, desenvolvimento e conclusão."
    )
    resposta = responder_pergunta_com_versiculo(prompt)
    esboco = montar_esboco(resposta, "estudo", 3)
    citacoes = buscar_autores(tema, autor)
    return {
        "tema": tema,
        "versiculos": versiculos,
        "autor": autor,
        "esboco": esboco,
        "citacoes": citacoes,
        "texto_gerado": resposta
    }


def gerar_devocional(tema, versiculo, autor=None):
    prompt = (
        f"Crie um devocional sobre '{tema}' baseado no versículo {versiculo}. "
        "Inclua uma reflexão pessoal e uma oração final."
    )
    resposta = responder_pergunta_com_versiculo(prompt)
    esboco = montar_esboco(resposta, "devocional", 2)
    citacoes = buscar_autores(tema, autor)
    return {
        "tema": tema,
        "versiculo": versiculo,
        "autor": autor,
        "esboco": esboco,
        "citacoes": citacoes,
        "texto_gerado": resposta
    }


def gerar_ebook(tema, capitulos, autor=None):
    prompt = (
        f"Crie um ebook sobre '{tema}' dividido em {capitulos} capítulos. "
        (
            (
                "Cada capítulo deve abordar um aspecto do tema "
                "e incluir referências bíblicas "
                f"e citações de {autor or 'teólogos relevantes'}."
            )
        )
    )
    resposta = responder_pergunta_com_versiculo(prompt)
    esboco = montar_esboco(resposta, "ebook", capitulos)
    citacoes = buscar_autores(tema, autor)
    return {
        "tema": tema,
        "capitulos": capitulos,
        "autor": autor,
        "esboco": esboco,
        "citacoes": citacoes,
        "texto_gerado": resposta
    }
