def montar_esboco(texto, tipo, num_topicos):
    partes = texto.split("\n")
    esboco = [p for p in partes if p.strip()][:num_topicos]
    return esboco
