def buscar_autores(tema, autor=None):
    if autor:
        return [f"{autor} sobre {tema}: 'A verdade bíblica é eterna.'"]
    return [
        (
            f"Agostinho sobre {tema}: "
            "'Nosso coração está inquieto enquanto não repousa em Ti.'"
        ),
        f"Calvino sobre {tema}: 'Toda sabedoria vem da Escritura.'"
    ]
